#ifndef MODEL_CLASS_H
#define MODEL_CLASS_H


class Cylinder{
private:
	double scale;
	double radius;
	double length;
	double contrast;
	double background;
public:
	Cylinder();
	double operator()(double q);
};

#endif
