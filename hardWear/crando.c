
#include<Python.h>
#include<stdint.h>
#include<math.h>

struct Random{
	int64_t a,b,c,d;
};

struct Random rng = {0};

void doCycle(void){
	rng.a ^= rng.b + 1 + rng.d;
	rng.b ^= (rng.a >> 6) + (rng.a << 7);
	rng.c ^= rng.c ^ rng.a;
	rng.d ^= (rng.d >> 16) + (rng.d << 17);
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
	uint64_t value = 0;
	if(range != 0)value = rng.a % range;
	value += lower;
	return PyLong_FromLong(value);
}

double cycleDouble(void){
	doCycle();
	double out = 0.0f;
	double Two = 2.0f;
	double One = 1.0f;
	uint64_t *outP = (uint64_t*)&out;
	uint64_t *OneP = (uint64_t*)&One;
	uint64_t *TwoP = (uint64_t*)&Two;
	(*TwoP)--;

	*outP = rng.a;
	*outP &= *TwoP;
	*outP |= *OneP;
	out -= 1.0d;
	return out;
}
PyObject *getFloat(PyObject *self,PyObject *args){
	return PyFloat_FromDouble(cycleDouble());
}

PyObject *getRangeFloat(PyObject *self,PyObject *args){
	double lower,upper;
	int ok = PyArg_ParseTuple(args,"dd",&lower,&upper);
	double out = cycleDouble();
	double range = upper - lower;
	out = out * range;
	out += lower;
	return PyFloat_FromDouble(out);
}


static PyMethodDef RandoDef[] = {
	{"float",getFloat,METH_NOARGS,"get Random Float [0-1.0)"},
	{"frange",getRangeFloat,METH_VARARGS,"get Range of Float"},
	{"random",getRandom,METH_VARARGS,"get Random"},
	{"irange",getRange,METH_VARARGS,"get in range"},
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
