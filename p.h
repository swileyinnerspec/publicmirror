//STP is a minimalist line protocol (feildbus) 
//for sharing dictionararies between automations
//some keys are reserved:
//_n where n is an integer: are functions that return key names
//__NAME__ is a globaly unique hostname (or atleast unique to the gateway)
//__DATE__ is a function that returns the date the automation was generated
//__HELP_n is a constant human readable label
//__CONFIG_STATE__ is a (optional) delimeted list of names representing the configuration vector, if not specified it is the difference of all reported names and the process name list
//__PROCES_STATE__ is a list of names that make up the instintainious proces state vector (process values, counters, setpoints etc.)
//__REPORT_PROC__ a tunable ratio period for pushing process vector  0 is never and 1 is always 0.5 is probably reasonable
#ifndef P_H
#define P_H 1
#include <string.h>
#include <ctype.h>
#include <stdlib.h>//would be nice to remove string and stdlib
#include <stdio.h>//only one sprintf, maybe think about replacing.
#ifndef MAX_INT
#endif
#define DELIM ' '
#define RESET '+'
#define MTERM '\n'
//need 80 bytes of ram for lexer
//int dict needs 2k of ram for dict + ~70 bytes of stack for other stuff
char *strctok(char *s,char d){//heh
	static char buff[40]={0};
	static char *olds=NULL;
	if(s!=NULL){
		olds=s;
	}
	if(olds!=NULL){
		int i=0;
		if(*olds==d)
			olds++;
		for(i=0;*olds!=d&&*olds!='\0'&&i<40;i++,olds++)
			buff[i]=*olds;
		buff[i]=0;
		if(i<=1){olds=NULL;return NULL;}
		return buff;
	}else return NULL;
}
//define tx function yourself
extern void print(char *);
#ifndef __AVR__
char *ftoa(double a,char *b){sprintf(b,"%f",a);b[9]='\0';return b;}
#endif
#ifdef __AVR__
char *ftoa(double a,char *b){dtostrf(a,7,4,b);b[9]='\0';return b;}
#endif
void stl_query(char *k){print("+");print(k);print("\n");}
void stl_send(char *k,char *v){ print("+");print(k);print(" ");print(v);print("\n"); }
void stl_sendi(char *k,int v){static char vbuff[10];stl_send(k,itoa(v,vbuff,10));}
//Recommended user dictionary for doubles as vals
#ifdef STL_USE_INT_DICT
char *stl_help[20]={0};
char *stl_names[256]={0};
char *stl_name="unkown";
double stl_vals[256];
double stl_report_period=100;
char *stl_process_state="";
char *stl_config_state="";
int stl_namecnt(void){
	int i=0;
	for(i=0;i<255;i++){
		if(stl_names[i]==NULL)
			break;
	}
	return i;
}
int stl_namei(char *k) {
	int i=0;
	for(i=0;i<255;i++){
		if(stl_names[i]!=NULL&&!strcmp(stl_names[i],k))
			break;
	}
	if(stl_namecnt()<255){
		//TODO: add names (either need alloc or some buffer)
	}
	return i;
}
void stl_set(char *k, char *v){
	if(k[0]=='_'){
		if(!strcmp(k,"__REPORT_PERIOD__"))
			stl_report_period=atof(v);
#ifdef nameevent
		nameevent(k+1);
#endif
		return;
	}
	int i=stl_namei(k);
#ifdef setevent
	setevent(k,v);//event driven stuff here
#endif
	if(i<255)
		stl_vals[i]=atof(v);
}
char *stl_get(char *k){
		if(!strcmp(k,"__DATE__"))
			return __DATE__;
		if(!strcmp(k,"__NAME__"))
			return stl_name;
		if(!strcmp(k,"__PROCESS_STATE__"))
			return stl_process_state;
		if(!strcmp(k,"__CONFIG_STATE__"))
			return stl_config_state;
		if(!strcmp(k,"__REPORT_PERIOD__")){
			static char fbuff[10];
			return ftoa(stl_report_period,fbuff);
		}
		if(strstr(k,"__HELP_")){
			int i=atoi(k+strlen("__HELP_"));
			if(i<20&&i>0){
				char *h=stl_help[i];
				if(h!=NULL)
					return h;
				else
					return "";
			}else{
				return "";
			}
		} if(k[0]!='_'){
			int i=stl_namei(k);
			static char vbuff[10]={0};
			if(i<255){
				ftoa(stl_vals[i],vbuff);
				return vbuff;
			}
			return "_None";
		}else{
			if(stl_names[atoi(k+1)]!=NULL){
				print(stl_names[atoi(k+1)]);
				return stl_names[atoi(k+1)];
			}else
				return "";
		}
}
void stl_report(void){
	static double counter=0;
	counter=(counter+1);
	if(counter >=stl_report_period){ counter=0; }
	if(abs(counter-1)<0.2){

		char *pch;
		pch=strctok(stl_process_state,' ');
		do{stl_send(pch,stl_get(pch));
			pch = strctok(NULL,' ');
		}while(pch != NULL);
	}
}
#endif
//in retrospect I could have just accumulated a line and run strctok
//this comes out of the grammer directly though heh
void stl_recc_int(char next,void (*set)(char *k, char *v), char *(*get)(char *k)){//FSM -> regular grammer for state transfer language
	static char kbuff[40]={0};
	static char vbuff[40]={0};
	typedef enum{S_LAMBDA=0,S_K,S_V,S_W} t_parserstate;
	static t_parserstate state=S_LAMBDA;//lambda k v w linearly, to w on fail to lambda on \n 
	if(next==RESET)
		state=S_LAMBDA;
	switch(state){
		case S_LAMBDA: kbuff[0]='\0';vbuff[0]='\0';state=S_K;

		case S_K:
			switch(next){
				case RESET: state=S_LAMBDA;break; 
				case DELIM: kbuff[strlen(kbuff)]='\0';
						    state=S_V;
				break;
				case MTERM:
					    if(strlen(kbuff)==0){
						    state=S_LAMBDA;
						    break;
					    } else{
						    stl_send(kbuff,get(kbuff));
						    state=S_LAMBDA;
					    }
					    
				break;
				default: if(isalpha(next)||isdigit(next)||next=='_'){
						if(strlen(kbuff)>40){
							state=S_W;
						}else{
							kbuff[strlen(kbuff)+1]='\0';
							kbuff[strlen(kbuff)]=next;//heh
						}
					 }else{state=S_W;}
			}break;
		case S_V:
			switch(next){
				case RESET: state=S_LAMBDA;break; 
				case MTERM:
					    if(strlen(vbuff)==0){
						    //we dont transmit
						    //there should be no
						    //delimiter
						    state=S_LAMBDA;
						    break;
					    } else{
						    set(kbuff,vbuff);
						    state=S_LAMBDA;
					    }
				break;
				default: 
					if(strlen(vbuff)>40){
						state=S_W;
					}else{
						vbuff[strlen(vbuff)+1]='\0';
						vbuff[strlen(vbuff)]=next;//heh
					}
			}break;
		case S_W: if(next==MTERM||next==RESET) state=S_LAMBDA; break;
	}
}
#ifdef STL_USE_INT_DICT
void stl_recc(char next){ stl_recc_int(next,stl_set, stl_get);}
#endif
#endif
