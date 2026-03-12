#define FL __FILE__,__LINE__
#define PD printf("."); fflush(stdout)
#define tz(x) if(x){printf("\n%s:%d:5:Fail: %s is %d not zero.",FL,#x,x);}else PD;
#define tde(x,y) if(x!=y){printf("\n%s:%d:6:Fail: %s is %d not %d.",FL,#x,x,y);}else PD;
#define tse(x,y) if(strcmp(x,y)){printf("\n%s:%d:6:Fail: %s is %s not %s",FL,#x,x,y);}else PD;

