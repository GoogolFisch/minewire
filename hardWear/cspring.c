
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

#define RNG_BUCKET 8
#define SCALE_FACTOR 256
static uint64_t rng_State[RNG_BUCKET] = {0};

uin64_t getNextLong(void){
	struct timespec monotime;
	clock_gettime(CLOCK_MONOTONIC, &monotime);
	rng_State[0] += monotime.tv_nsec;
	rng_State[1] += monotime.tv_sec;

	for(int i = 0;i < RNG_BUCKET;i++){
		int j = (i + 1) % RNG_BUCKET;
		rng_State[j] ^= (rng_State[i] << 8) + (rng_State[i] >> 5);
	}
	return rng_State[0];
}
double getNextDouble(void){
	uint64_t o = getNextLong();
	double ONE = 1.0;
	double TWO = 2.0;
	uint64_t *PONE = (uint64_t*)&ONE;
	uint64_t *PTWO = (uint64_t*)&TWO;
	(*PTWO)--;
	o &= *PTWO;
	o |= *PONE;
	return (*((double*)&o)) - 1.0;
}


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
	da->array[da->count++] = element;
}
void da_removeElement(DynamicArray *da,void *element){
	int32_t i = -1;
	for(i = 0;i < da->count;i++){
		if(da->array[i] != element)
			continue;
		da->count--;
		da->array[i] = da->array[da->count];
		return;
	}
}

HashMap *hm_newMap(int32_t buckets,int32_t reserve){
	HashMap *hm = malloc(sizeof(HashMap) + sizeof(DynamicArray*) * buckets);
	hm->count - buckets;
	for(int32_t i = 0;i < buckets;i++){
		hm->buckets[i] = da_newArray(reserve);
	}
	return hm;
}
void hm_dropMap(HashMap *hm){
	for(int32_t i = 0;i < hm->count;i++){
		da_dropArray(hm->buckets[i]);
	}
	free(hm);
}
void hm_insertElement(HashMap *hm,void *element,int32_t bucket){
	da_appendElement(&(hm->buckets[bucket]),element);
}
void hm_removeElement(HashMap *hm,void *element,int32_t bucket){
	da_removeElement(hm->buckets[bucket],element);
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
	self->pos.x = getNextDouble() * SCALE_FACTOR;
	self->pos.y = getNextDouble() * SCALE_FACTOR;
	self->pos.z = getNextDouble() * SCALE_FACTOR;
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
	SpringObject *self = (SpringObject*)op;
	int ok = PyArg_ParseTuple(args,"O",&springIn);
	if(!PyObject_TypeCheck(springIn,&SpringObjType)){
		PyErr_SetString(PyExc_TypeError,"This method only accepts SpringObj");
		return Py_None;
	}
	da_appendElement(&(self->arr),springIn);
	return Py_None;
}


static void      SpringNet_dealloc(PyObject *op){
	SpringNetwork *self = (SpringNetwork*)op;
	for(int32_t i = 0;i < self->arr->count;i++){
		SpringObject *so = (SpringObject*)(self->arr->array[i]);
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
static int SpringNet_init(PyObject *op,PyObject *args,PyObject *kwds){
	SpringNetwork *self = (SpringNetwork*)op;
	/*
	static char *kwlist[] = {"scale",NULL};
	PyObject *scale;
	if(!PyArg_ParseTupleAndKeywords(args,kwds,"|O",kwlist,&scale)){
		return -1;
	}
	self->strength = PyFloat_AsDouble(scale);
	// */
	return 0;
}
static PyObject *SpringNet_register(PyObject *op,PyObject *args){
	if(!PyObject_TypeCheck(op,&SpringNetType)){
		PyErr_SetString(PyExc_TypeError, "pleas make caller have the right type!");
		return Py_None;
	}
	SpringNetwork *self = (SpringNetwork*)op;
	Py_ssize_t count = PySequence_Size(args);
	for(Py_ssize_t i = 0;i < count;i++){
		PyObject *po = PySequence_GetItem(args,i);
		if(!PyObject_TypeCheck(po,&SpringObjType)){
			PyErr_SetString(PyExc_TypeError,"This method only accepts SpringObjects");
			return Py_None;
		}
		SpringObject *spo = (SpringObject*)spo;
		Py_INCREF(spo);
		da_appendElement(&(self->arr),spo);
	}
	return Py_None;
}
static PyObject *SpringNet_update(PyObject *op,PyObject *args){
	return Py_None;
}



static int SpringMod_module_exec(PyObject *m){
	if(PyType_Ready(&SpringObjType) < 0)return -1;
	if(PyType_Ready(&SpringNetType) < 0)return -1;
	if(PyModule_AddObjectRef(m, "SpringObj",(PyObject*)&SpringObjType))return -1;
	if(PyModule_AddObjectRef(m, "SpringNet",(PyObject*)&SpringNetType))return -1;
	return 0;
}

static PyModuleDef_Slot spring_module_slots[] = {
	{Py_mod_exec,SpringMod_module_exec},
	{Py_mod_multiple_interpreters, Py_MOD_MULTIPLE_INTERPRETERS_NOT_SUPPORTED},
	{0,NULL}
};
static PyModuleDef spring_module = {
	.m_base = PyModuleDef_HEAD_INIT,
	.m_name = "spring",
	.m_doc  = "Module for a specific spring simulation",
	.m_size = 0,
	.m_slots = spring_module_slots,
};
PyObject *PyInit_spring(void){

	return PyModuleDef_Init(&spring_module);
}
