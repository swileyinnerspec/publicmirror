//This will calculate a sample from a normal distribution iteratively.
#include <stdio.h>
#include <stdlib.h>


int nr(int it,int (*rand)(void)){
	int count=0;
	for(;it>0;it--){
		if(rand() >RAND_MAX/2) count++;
		else count--;
	}
	return count;
}
double snr(void) {
	const int itr=255;
	const double oldmean=itr/2.;
	const double oldvar=itr/4.;

	return nr(itr,rand)/oldvar;
}
int main(int argc,char **argv) {srand(atoi(argv[1]));printf("%f\n",snr());return 0;}
