
#include<Python.h>
#include<stdint.h>
#include<math.h>
#include<signal.h>
#include<stddef.h>
#include<stdlib.h>

struct Vector;
struct DynamicArray;
struct HashMap;
struct SpringObj;
struct SpringNet;


static void SpringObj_dealloc(PyObject *op);
static PyObject *SpringObj_new(PyTypeObject *type,PyObject *args,PyObject *kwds);
static int SpringObj_init(PyObject *op,PyObject *args,PyObject *kwds);
static PyObject *SpringObj_getPosition(PyObject *op,void *closure);
static int SpringObj_setPosition(PyObject *op,PyObject *value,void *closure);
static PyObject *SpringObj_addSpringForce(PyObject *op,PyObject *args);






////////
typedef struct Vector {
	double x,y,z;
} Vector;

typedef struct DynamicArray{
	uint32_t size;
	uint32_t count;
	void *array[];
} DynamicArray;

typedef struct HashMap {
	uint32_t count;
	DynamicArray *buckets;
} HashMap;

typedef struct SpringObj {
	PyObject_HEAD;
	PyObject *farRef;
	Vector pos;
	Vector vel;
	Vector targeting;
	struct SpringNet *parent;
	DynamicArray *attract;
} SpringObject;

typedef struct SpringNet {
	PyObject_HEAD;
	DynamicArray *arr;
} SpringNetwork;


static PyMemberDef SpringObj_members[] = {
    {NULL}
};

static PyGetSetDef SpringObj_getsetters[] = {
	{"pos",SpringObj_getPosition,SpringObj_setPosition,"the position of this thing",NULL},
	{NULL}
};
static PyMethodDef SpringObj_methods[] = {
	{"addSpring",SpringObj_addSpringForce,METH_NOARGS,"Add a spring to the force Network"},
	{NULL}
};

static PyTypeObject SpringObjType = {
	.ob_base = PyVarObject_HEAD_INIT(NULL,0)
	.tp_name = "spring.SpringObj",
	.tp_doc = PyDoc_STR("Springs Object"),
	.tp_basicsize = sizeof(SpringObject),
	.tp_itemsize = 0,
	.tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
	.tp_new = SpringObj_new,
	.tp_init = SpringObj_init,
	.tp_dealloc = SpringObj_dealloc,
	.tp_members = SpringObj_members,
	.tp_methods = SpringObj_methods,
	.tp_getset = SpringObj_getsetters,
};




int32_t hm_getBucket(HashMap *hm,Vector *v){
#define DOUB_TO_INT(x) ((int32_t)((x) / 4.0))
	int32_t b = DOUB_TO_INT(v->x);
	b += 64 * DOUB_TO_INT(v->x);
	b += 64 * 64 * DOUB_TO_INT(v->x);
	b %= hm->count;
#undef DOUB_TO_INT
	return b;
}

void vec_moveVector(Vector *pos,Vector *vel,int32_t count){
	double over = 1.0 / (double)count;
	pos->x += over * vel->x;
	pos->y += over * vel->y;
	pos->z += over * vel->z;
	if(pos->x < 1.0)pos->x = 1.0;
	if(pos->y < 0.0)pos->y = 0.0;
	if(pos->z < 1.0)pos->z = 1.0;
}
double vec_magnitudeSquare(Vector *origin,Vector *goal){
#define DOUB_SQ_MAX(out,x) if(out < (x) * (x))out = (x) * (x)
	double out = 0.0;
	DOUB_SQ_MAX(out,origin->x - goal->x);
	DOUB_SQ_MAX(out,origin->y - goal->y);
	DOUB_SQ_MAX(out,origin->z - goal->z);
#undef DOUB_SQ_MAX
	return out;
}
void vec_setToZero(Vector *vec){
	vec->x = 0;
	vec->y = 0;
	vec->z = 0;
}






static void SpringObj_dealloc(PyObject *op){
	SpringObject *self = (SpringObject*)op;
	if(self->parent != NULL)
		// Delayed Free
		return;
	Py_TYPE(self)->tp_free(self);
	return;
}
static PyObject *SpringObj_new(PyTypeObject *type, PyObject *args,PyObject *kwds){
	SpringObject *self;
	self = (SpringObject*) type->tp_alloc(type,0);

	self->farRef  = NULL;
	self->parent  = NULL;
	self->pos = (Vector){0};
	self->vel = (Vector){0};
	self->targeting = (Vector){0};
	self->attract = NULL;

	if(self == NULL){
		return NULL; 
SpringObj_Error:
		if(self->attract != NULL)free(self->attract);
		Py_DECREF(self);
		return NULL;
	}
	self->attract = malloc(sizeof(DynamicArray));
	if(self->attract == NULL)goto SpringObj_Error;

	return (PyObject*)self;
}
static int SpringObj_init(PyObject *op,PyObject *args,PyObject *kwds){
	SpringObject *self = (SpringObject*)op;
	static char *kwlist[] = {"network","preLay",NULL};
	PyObject *network = NULL;
	PyObject *farRef = NULL;
	if(!PyArg_ParseTupleAndKeywords(args,kwds,"|OO",kwlist,&network,&farRef)){
		return -1;
	}
	// I don't want to manage the DEC_REF
	self->parent = (SpringNetwork*)network;
	self->farRef = farRef;
	return 0;
}
static PyObject *SpringObj_getPosition(PyObject *op,void *closure){
	SpringObject *self = (SpringObject *) op;
	PyObject *tupleOut = PyTuple_New(3);
	PyTuple_SET_ITEM(tupleOut,0,PyLong_FromLong((int64_t)self->pos.x));
	PyTuple_SET_ITEM(tupleOut,1,PyLong_FromLong((int64_t)self->pos.y));
	PyTuple_SET_ITEM(tupleOut,2,PyLong_FromLong((int64_t)self->pos.z));
	return tupleOut;
}
static int SpringObj_setPosition(PyObject *op,PyObject *value,void *closure){
	SpringObject *self = (SpringObject*)op;
	int ok = PyArg_ParseTuple(value,"ddd",
			&(self->pos.x),
			&(self->pos.y),
			&(self->pos.z));
	printf("%i\n",ok);
	return 0;
}




