#include <stdio.h>

int main(int argc, char **argv) {
	char *out="0\n";
	char *path="/sys/class/leds/green:indicator/brightness";
	if(argc >1){
		out="1\n";
		if(argv[1][0]=='s'){
			char buf[10];
			FILE *f=fopen(path,"r");
			fread(buf,10,1,f);
			buf[2]='\0';
			printf("%s",buf);
			return 0;
		}
	}
	FILE *f=fopen(path,"w");
	if(f==NULL)
		return 1;
	fprintf(f,"%s",out);
	return 0;
}
