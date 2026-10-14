
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


static void      SpringObj_dealloc(PyObject *op);
static PyObject *SpringObj_new(PyTypeObject *type,PyObject *args,PyObject *kwds);
static int       SpringObj_init(PyObject *op,PyObject *args,PyObject *kwds);
static PyObject *SpringObj_getPosition(PyObject *op,void *closure);
static int       SpringObj_setPosition(PyObject *op,PyObject *value,void *closure);
static PyObject *SpringObj_addSpringForce(PyObject *op,PyObject *args);

static void      SpringNet_dealloc(PyObject *op);
static PyObject *SpringNet_new(PyTypeObject *type,PyObject *args,PyObject *kwds);
static int       SpringNet_init(PyObject *op,PyObject *args,PyObject *kwds);
static PyObject *SpringNet_register(PyObject *op,PyObject *args);
static PyObject *SpringNet_update(PyObject *op,PyObject *args);





////////
typedef struct Vector {
	double x,y,z;
} Vector;

typedef struct DynamicArray{
	uint32_t size;
	uint32_t count;
	void    *array[];
} DynamicArray;

typedef struct HashMap {
	uint32_t      count;
	DynamicArray *buckets[];
} HashMap;

typedef struct SpringObj {
	PyObject_HEAD;
	Vector            pos;
	Vector            vel;
	Vector            targeting;
	struct SpringNet *parent;
	DynamicArray     *attract;
} SpringObject;

typedef struct SpringNet {
	PyObject_HEAD;
	HashMap      *hmap;
	DynamicArray *arr;
} SpringNetwork;


static PyMemberDef SpringObj_members[] = {{NULL}};
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



static PyMemberDef SpringNet_members[] = {{NULL}};
static PyGetSetDef SpringNet_getsetters[] = {{NULL}};
static PyMethodDef SpringNet_methods[] = {
	{"register",SpringNet_register,METH_NOARGS,"Register a node to the network"},
	{"update",  SpringNet_update  ,METH_NOARGS,"Update the whole network!"},
	{NULL}
};
static PyTypeObject SpringNetType = {
	.ob_base = PyVarObject_HEAD_INIT(NULL,0)
	.tp_name = "spring.SpringNet",
	.tp_doc = PyDoc_STR("Springs in a Network"),
	.tp_basicsize = sizeof(SpringNetwork),
	.tp_itemsize = 0,
	.tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
	.tp_new = SpringNet_new,
	.tp_init = SpringNet_init,
	.tp_dealloc = SpringNet_dealloc,
	.tp_members = SpringNet_members,
	.tp_methods = SpringNet_methods,
	.tp_getset = SpringNet_getsetters,
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

DynamicArray *da_newArray(int32_t reserve){
	DynamicArray *dao = malloc(sizeof(DynamicArray) + reserve * sizeof(void*));
	dao->size = reserve;
	dao->count = 0;
	return dao;
}
void da_dropArray(DynamicArray *da){
	free(da);
}
void da_appendElement(DynamicArray **array,void *element){
	DynamicArray *da = *array;
	if(da->count >= da->size){
		da->size *= 2;
		*array = realloc(da,sizeof(DynamicArray) + da->size * sizeof(void*));
		da = *array;
	}
	da->arr[da->count++] = element;
}
void da_removeElement(DynamicArray *da,void *element){
	int32_t i = -1;
	for(i = 0;i < da->count;i++){
		if(da->arr[i] != element)
			continue;
		da->count--;
		da->arr[i] = da->arr[da->count];
		return;
	}
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
	self->attract = da_newArray(8);
	if(self->attract == NULL)goto SpringObj_Error;

	return (PyObject*)self;
}
static int SpringObj_init(PyObject *op,PyObject *args,PyObject *kwds){
	SpringObject *self = (SpringObject*)op;
	static char *kwlist[] = {"network","preLay",NULL};
	PyObject *network = NULL;
	if(!PyArg_ParseTupleAndKeywords(args,kwds,"|O",kwlist,&network)){
		return -1;
	}
	// I don't want to manage the DEC_REF
	self->parent = (SpringNetwork*)network;
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
static PyObject *SpringObj_addSpringForce(PyObject *op,PyObject *args){
	PyObject *springIn;
	SpringObj *self = (SpringObj*)op;
	int ok = PyArg_ParseTuple(args,"O",&springIn);
	return Py_None;
}


static void      SpringNet_dealloc(PyObject *op){
	SpringNetwork *self = (SpringNetwork*)op;
	for(int32_t i = 0;i < self->arr->count;i++){
		SpringObj *so = (SpringObj*)(self->arr->array[i]);
		so->parent = NULL;
		Py_DECREF(so);
	}
	free(self->arr);
	//
	for(int32_t i = 0;i < self->hmap->count;i++){
		free(self->hmap->buckets);
	}
	free(self->hmap);
	//
	Py_TYPE(self)->tp_free(self);
	return;
}
static PyObject *SpringNet_new(PyTypeObject *type,PyObject *args,PyObject *kwds){
	SpringNetwork *self;
	self = (SpringNetwork*)type->tp_alloc(type,0);

	self->hmap = NULL;
	self->arr = NULL;

	if(self == NULL){
		return NULL; 
SpringObj_Error:
		if(self->arr != NULL)da_dropArray(self->arr);
		Py_DECREF(self);
		return NULL;
	}
	self->arr = da_newArray(128);
	if(self->arr == NULL)goto SpringObj_Error;

	return (PyObject*)self;
}




static PyModuleDef spring_module = {
	.m_base = PyModuleDef_HEAD_INIT,
	.m_name = "spring",
	.m_doc  = "Module for a specific spring simulation",
	.m_size = 0,
	//.m_slots = 
};
static PyObject *PyInit_spring(void){
	return PyModuleDef_Init(&spring_module);
}
