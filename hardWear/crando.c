
#include<Python.h>
#include<stdint.h>

struct Random{
	int64_t a,b,c,d;
};

struct Random rng = {0};

void doCycle(void){
	rng.a ^= rng.b + 1 + rng.d;
	rng.b ^= (rng.a >> 6) + (rng.a << 7);
	rng.c ^= rng.c ^ rng.a;
	rng.d ^= (rng.d >> 6) + (rng.d << 7);
}

PyObject *getRandom(PyObject *self,PyObject *args) {
	uint64_t value = 0;
	if(PySequence_Size(args) > 0){
		int ok = PyArg_ParseTuple(args,"L",&value);
	}
	doCycle();
	rng.a ^= value;
	return PyLong_FromLong(rng.a);
}

PyObject *getRange(PyObject *self,PyObject *args) {
	uint64_t lower,upper;
	lower = 0;
	upper = 0;
	Py_ssize_t size = PySequence_Size(args);
	int ok = 0;
	if(size == 1) ok = PyArg_ParseTuple(args,"L",&upper);
	if(size == 2) ok = PyArg_ParseTuple(args,"LL",&lower,&upper);
	uint64_t range = upper - lower;
	doCycle();
	uint64_t value = rng.a % range;
	value += lower;
	return PyLong_FromLong(value);
}


static PyMethodDef RandoDef[] = {
	{"random",getRandom,METH_VARARGS,"get Random"},
	{"range",getRange,METH_VARARGS,"get in range"},
	{NULL,NULL,0,NULL}
};

static PyModuleDef
RandoMod = {
	PyModuleDef_HEAD_INIT,
	"random number generator",
	"",
	-1,
	RandoDef,
};

PyObject* PyInit_rando()
{
	PyObject *outModule = PyModule_Create(&RandoMod);
	if(outModule == NULL){
		return NULL;
mod_final_fail:
		Py_DECREF(outModule);
		return NULL;
	}
	return outModule;
}
