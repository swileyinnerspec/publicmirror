//Kanban boards
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
//#define DBLINE //
#define DBLINE 
enum state_t {TODO =1, DOING, DONE,WONT};
char *state_strings[] = { "INVALID", "TODO","DOING","DONE","WONT"};
enum type_t {TICKET=1, COMMENT,EPIC,SCRUM};
char *type_strings[] = { "INVALID", "TICKET","EPIC","SCRUM"};
#define MAXCOMMENTS 20
typedef struct {
 char *name;
 char *desc;
 char *closemesg;
 char *assignee;
 char *reporter;
 char *scrum;
 int type;
 int state;
 int points;
 int priority;
 char *parent;
 time_t otime;
 time_t dtime;
 time_t ctime;
 time_t etime;
 int ephemeral;
 char *comments[MAXCOMMENTS];
 int commentcount;
} ticket;

#define MAX_TICKETS 10000
ticket tickets[MAX_TICKETS];
int lastticket=-1;
int multiusermode=1;
char *scrum="";
int fortnight=86400*14;
char *dbpath;
char *adbpath;
int savedb=0;
int indexforname(char *name){
	for(int i=0;i<=lastticket;i++)if(!strcmp(name,tickets[i].name))return i;
	return -1;
}
void error(char *m,int n){
	printf("%s,%d\n",m,n);
	exit(1);
}
void check(int expression, char *m) {if(!expression){error(m,expression);}}
void invalidkey(int lnum,char *name,char *key,char *val){
	printf("#Incompatible Datum at line number:%d will be dropped.\n",lnum);
	if(!strcmp(name,"global")) printf("%s=%s\n#Hint:open a [ticket] first.",key,val);
	else printf("[%s]\n%s=%s\n",name,key,val);
}
void updatesetting(int lnum,char *l){
	if(index(l,'=')==NULL) return;
	char *val=strdup(index(l,'=')+1);
	val[strlen(val)-1]='\0';
	*index(l,'=')='\0';
	if(!strcasecmp(l,"scrum"))scrum=val;
	else{//free val
		if(!strcasecmp(l,"fortnight"))fortnight=atoi(val);
		else if(!strcasecmp(l,"multiusermode"))multiusermode=atoi(val);
		else invalidkey(lnum,"global",l,val);
		free(val);
	}
}
void updatefield(int lnum,char *l,int t){
	if(index(l,'=')==NULL) return;
	char *val=strdup(index(l,'=')+1);//TODO: Handle comments
	val[strlen(val)-1]='\0';
	*index(l,'=')='\0';
	if(!strcmp(l,"desc"))tickets[t].desc=val;
	else if(!strcasecmp(l,"assignee"))tickets[t].assignee=val;
	else if(!strcasecmp(l,"reporter"))tickets[t].reporter=val;
	else if(!strcasecmp(l,"parent"))tickets[t].parent=val;
	else if(!strcasecmp(l,"closemesg"))tickets[t].closemesg=val;
	else if(!strcasecmp(l,"scrum"))tickets[t].scrum=val;
	else if(l[0]=='#'){
		if(tickets[t].commentcount<MAXCOMMENTS){
			tickets[t].commentcount++;
			tickets[t].comments[tickets[t].commentcount-1]=val;
		}else{
			error("too many comments at line",lnum);
		}
	}else {//We will free val since we're not keeping it
		if(!strcasecmp(l,"state")){
			if(!strcasecmp(val,"TODO"))tickets[t].state=TODO;
			else if(!strcasecmp(val,"DOING"))tickets[t].state=DOING;
			else if(!strcasecmp(val,"WONT"))tickets[t].state=WONT;
			else if(!strcasecmp(val,"DONE"))tickets[t].state=DONE;
			else invalidkey(lnum,tickets[t].name,l,val);
		}else if(!strcasecmp(l,"type")){
			if(!strcasecmp(val,"TICKET"))tickets[t].type=TICKET;
			else if(!strcasecmp(val,"EPIC"))tickets[t].type=EPIC;
			else if(!strcasecmp(val,"SCRUM"))tickets[t].type=SCRUM;
			else invalidkey(lnum,tickets[t].name,l,val);
		} else if(!strcasecmp(l,"points"))tickets[t].points=atoi(val);
		else if(!strcasecmp(l,"otime"))tickets[t].otime=atoi(val);
		else if(!strcasecmp(l,"dtime"))tickets[t].dtime=atoi(val);
		else if(!strcasecmp(l,"ctime"))tickets[t].ctime=atoi(val);
		else if(!strcasecmp(l,"etime"))tickets[t].etime=atoi(val);
		else if(!strcasecmp(l,"priority"))tickets[t].priority=atoi(val);
		else{puts("very");invalidkey(lnum,tickets[t].name,l,val);}
		free(val);
	}
}
void readintickets(FILE *f){
	char curline[500];
	int lcount=0;
	int curticket=-1;
	while(!feof(f)){
		fgets(curline,500,f);
		lcount++;
		if(curline[0]=='['){
			curline[strlen(curline)-2]='\0';
			if(!strcmp(curline+1,"global")) curticket=-1;
			else if(indexforname(curline+1)>=0){
				printf("#Note: duplicate ticket on line %d. Updating ticket. New data will overwrite old.\n",lcount);
				curticket=indexforname(curline+1);
			}else{
				lastticket++;
				memset(tickets+lastticket,0,sizeof(ticket));
				tickets[lastticket].name=strdup(curline+1);
				curticket=lastticket;
			}
		}else if(curticket>=0){
			updatefield(lcount,curline,curticket);
		}else updatesetting(lcount,curline);
	}
}
void writeoutticket(FILE *f,ticket t){
	fprintf(f,"[%s]\n",t.name);
	fprintf(f,"desc=%s\n",t.desc);
	if(t.assignee!=NULL) fprintf(f,"assignee=%s\n",t.assignee);
	if(t.reporter!=NULL) fprintf(f,"reporter=%s\n",t.reporter);
	if(t.parent!=NULL) fprintf(f,"parent=%s\n",t.parent);
	if(t.scrum!=NULL) fprintf(f,"scrum=%s\n",t.parent);
	fprintf(f,"state=%s\n",state_strings[t.state]);
	fprintf(f,"type=%s\n",type_strings[t.type]);
	//fprintf(f,"state=%d\n",t.state);
	//fprintf(f,"type=%d\n",t.type);
	fprintf(f,"points=%d\n",t.points);
	if(t.otime) fprintf(f,"otime=%ld\n",t.otime);
	if(t.dtime) fprintf(f,"dtime=%ld\n",t.dtime);
	if(t.ctime) fprintf(f,"ctime=%ld\n",t.ctime);
	if(t.etime) fprintf(f,"etime=%ld\n",t.etime);
	if(t.priority) fprintf(f,"priority=%d\n",t.priority);
	for(int i=0;i<t.commentcount ;i++){
		fprintf(f,"%s\n",t.comments[i]);
	}
}
void writeoutdb(FILE *f) {
	int tcount=0;
	fprintf(f,"#autogenerated from tt\nmultiusermode=%d\nscrum=%s\n",multiusermode,scrum);
	for(int i=0;i<=lastticket;i++){
		if(!tickets[i].ephemeral){
			tcount++;
			writeoutticket(f,tickets[i]);
		}
	}
	printf("%d tickets written to database.\n",tcount);
}
void workflow(void) {
	printf("In kanban mode you should create a ticket as soon as a bug or unit of work is discovered. Before assigning it to an engineer, a number of relative \"points\" should be added as an intuitive measure of how difficult the ticket appears. This can help judge the health of the team and help other people make predictions for future work.\n");
	printf("Each day an emcee should run the kanban command and go through the tickets in the doing column for status updates to discover blocking problems and share advice. The report command may be used periodically to judge organizational effectiveness.\n");
	printf("Scrum mode uses a daily standup like kanban mode but in addition a new ticket should be generated and assigned to the manager. These should expire at the end of the period and be replaced. All current tasks should have their scrum field point to the current scrum. At the end of the period the report command can be used to judge effectiveness and find weakpoints. Automatically generating a burndown chart from the csv data should be easy.\n");
	printf("When used with a feature branch worklow on a VCS, branches should be named after the ticket. This way they can be found by running `git branch | grep ticketname`.\n");
	printf("Most people find a fortnight (two weeks) to be an effective scrum period. Remember that the data here is more for engineers to communicate with eachother and shouldn't be abused by managers, in general you shouldn't have formal requirements for numbers of points completed as they are entierly arbitrary. The productivity of the team and individuals will naturally ebb and flow, allowing the data to follow it makes measurement and planning possible.\n");
	printf("TT will not manage database history for you, a VCS tool like git is recommended for this.\n\n");
	printf("Useful automations:\n");
}
void usage(void){
	printf("tt tracks tickets in an INI formated databse at $TTDB or ./todo.ini\n");
	printf("USAGE: tt subcmd ticket [message]\n");
	printf("subcommand list:\n");
	printf(" check: load database and report errors\n");
	printf(" normalize: check database and write it back\n");
	printf(" create: create the specified ticket with $USER as reporter\n");
	printf(" assign: assign the specified ticket to assignee with points\n");
	printf(" bring: add specified ticket to current scrum.\n");
	printf(" do: move  the specified ticket to doing column\n");
	printf(" close: close the specified ticket with message as close message\n");
	printf(" show: write ticket to stdout\n");
	printf(" import: read tickets from stdin, overwritting data in db (missing data will merge, so you can run show followed by import and enter new values for the fields this way.)\n");
	printf(" kanban: show ticket summaries in swimlanes, tickets closed more than a scrum/fortnight ago will be hidden.\n");
	printf(" report: write out historical report for tickets one per line, if a scrum is specified the report will be restricted to it. Note that some tickets may have been moved to a new scrum. The difference in the scrum ticket points and the points of the closed tickets can tell you how many.\n"); 
	printf(" stats: write out statistics report for current tickets.\n"); 
	printf(" deadlines: write an appointment/calendar/diary file containing expiration dates for all tickets in the database\n");
	//printf(" delta: export tickets that differ between a joined (see below) db and the primary.\n");
	//printf("In addition the special \"join\" subcommand may precede others allowing the temporary joining of an archive file or external boards.\n");
	printf(" archive: move ticket to todo.old.ini.\n");
	printf(" workflow: advice on using tt in your workflow.\n");
	printf(" newscrum: generate a new scrum ticket with $USER as the assignee and set the current scrum to it.\n");
	printf("If scrum is set in global options some reports will be restricted to tickets in that scrum.\n");
	printf("\n");
}

void newticket(int argc, char **argv) {
	char name[500];
	char desc[500];
	if(argc<1){
		printf("The name of the ticket is the primary key, it should probably not have spaces if it is to be used by automations.\nname: ");
		fgets(name,500,stdin);
		name[strlen(name)-1]='\0';
	}else{strcpy(name,argv[0]);}
	if(indexforname(name)>0||!strcmp(name,"global")){printf("name already in use.\n");exit(-1);}
	if(argc<2){
		printf("The description message is a human readable description of the work to be done, you might include the path to a wiki entry if it is complex\ndesc: ");
		fgets(desc,500,stdin);
	}
	lastticket++;
	memset(tickets+lastticket,0,sizeof(ticket));
	tickets[lastticket].name=strdup(name);
	tickets[lastticket].desc=strdup(desc);
	tickets[lastticket].reporter=strdup(getenv("USER"));
	tickets[lastticket].otime=time(NULL);
	tickets[lastticket].state=TODO;
	tickets[lastticket].type=TICKET;
}
void delticket(int t) {
	check(t<=lastticket,"Ticket index is beyond end of ticket list");
	check(t>=0,"Ticket index is before beginning of ticket list");
	for(;t<lastticket;t++){
		tickets[t]=tickets[t+1];
	}
	lastticket-=1;
}
void assign(int argc, char **argv) {
	char assignee[500];
	char points[500];
	if(multiusermode){
		if(argc<1){printf("USAGE: assign ticket [assignee [points]]\n Assign a ticket to a worker and point it.\n"); exit(-1);}
		int t=indexforname(argv[0]);
		if(t<0){printf("no such ticket:%s\n",argv[0]);}
		argc--; argv++;
		if(argc<2){
			printf("The assignee will be responsible for completing the specified work unit, preferably before etime or the end of the scrum\nassignee: ");
			fgets(assignee,500,stdin);
			strcpy(assignee,strdup(argv[0]));
		}
	}
	if(argc<3){
		printf("The amount of \"points\" this work unit will take is only meaningful to your team. Often 1 means about a day or so and generally only prime numbers below 21 are considered meaningful. For larger units consider creating an \"epic\" ticket with children.\npoints: ");
		fgets(points,500,stdin);
	}
	int t=indexforname(argv[0]);
	tickets[t].assignee=strdup(assignee);
	tickets[t].points=atoi(points);
}
void doticket(int argc, char **argv){
	if(argc<1){printf("USAGE: do ticket\n Move ticket to \"Doing\" column.\n"); exit(-1);}
	int t=indexforname(argv[0]);
	if(t>0){
		tickets[t].state=DOING;
		tickets[t].dtime=time(NULL);
	} else printf("No such ticket.\n");
}
void closeticket(int argc, char **argv){
	if(argc<1){printf("USAGE: close ticket\n Move ticket to \"Done\" column.\n"); exit(-1);}
	int t=indexforname(argv[0]);
	if(t>0){
		tickets[t].state=DONE;
		tickets[t].ctime=time(NULL);
	} else printf("No such ticket.\n");
}
void showticket(int argc, char **argv){
	if(argc<1){printf("USAGE: show ticket\n Export ticket to stdout.\n"); exit(-1);}
	int t=indexforname(argv[0]);
	if(t>=0){
		writeoutticket(stdout,tickets[t]);
	} else printf("No such ticket.\n");
}
void reportswimlane(ticket t){
	for(int i=TODO;i<t.state;i++)
		printf("\t\t\t\t");
	if(multiusermode) printf("[%s @ %s : %d]\n",t.name,t.assignee,t.points);
	if(!multiusermode) printf("[%s : %d]\n",t.name,t.points);
}
void reportone(ticket t){
	printf("%s\t%d\t%ld\t%ld\n",t.assignee,t.points,t.ctime-t.otime,t.ctime-t.dtime);
}
void report(int argc, char **argv,int swimlane){
	char *scrumname=scrum;
	if(argc>1) scrumname=argv[0];
	if(swimlane) printf("TODO\t\t\t\tDOING\t\t\t\tDONE\n");
	else printf("ASIGNEE\tPOINTS\tTIMEOPEN\tTIMEDOING\n");
	for(int i=0;i<=lastticket;i++){
		if(scrumname==NULL||strcmp(scrumname,"")||tickets[i].scrum==NULL||!strcmp(tickets[i].scrum,scrumname)){
			if(swimlane) reportswimlane(tickets[i]);
			else reportone(tickets[i]);
		}
	}
}
void stats(void){ //TODO: allow statistics to be reported over sliding time window.
	char *scrumname=scrum;
	time_t t=time(NULL);
	long long catimetoclose=0;
	long long catimedoing=0;
	int totalcount=0;
	int opencount=0;
	int doingcount=0;
	int donecount=0;
	long long caage=0;//Average age of unclosed tickets
	const long long timediv=60*60;//an hour
	//TODO: weight by points.
	for(int i=0;i<=lastticket;i++){
		if(scrumname==NULL||strcmp(scrumname,"")||tickets[i].scrum==NULL||!strcmp(tickets[i].scrum,scrumname)){
			if(tickets[i].otime==0) continue; //tickets with otime of zero are ignored for statistics
			long long timetoclose=tickets[i].ctime-tickets[i].otime;
			long long timetodoing=tickets[i].dtime-tickets[i].otime;
			long long age=t-tickets[i].otime;
			if(tickets[i].state==DONE){
				catimetoclose=(timetoclose + (donecount*catimetoclose))/(donecount+1);
				donecount++;
			}else {
				caage=(age +(opencount*caage))/(opencount+1);
				opencount++;
			}
			if(tickets[i].state==DOING){
				catimedoing=(timetodoing + (doingcount*catimedoing))/(doingcount+1);
				doingcount++;
			}
			totalcount++;
		}
	}
	printf("toclose\ttodoing\tavg age\topen\tdoing\tdone\ttotal\t\t Time in hours.\n");
	printf("%lld\t%lld\t%lld\t%d\t%d\t%d\t%d\n",catimetoclose/timediv,catimedoing/timediv,caage/timediv,opencount,doingcount,donecount,totalcount);
}
void comment(int argc,char **argv){
	if(argc<2){printf("USAGE: comment ticket \"comment\"\n add a short comment to a ticket.\n"); exit(-1);}
	int t=indexforname(argv[0]);
	if(t>0){
		if( tickets[t].commentcount<MAXCOMMENTS){
			tickets[t].commentcount++;
			tickets[t].comments[tickets[t].commentcount-1]=strdup(argv[2]);
		}else { printf("Too many comments already.\n");exit(-2);}
	} else {printf("No such ticket.\n");exit(-1);}
}
void archive(int argc,char **argv){
	if(argc<1){printf("USAGE: archive ticket \n Move ticket to %s\n",adbpath); exit(-1);}
	int t=indexforname(argv[0]);
	if(t>0){
		FILE *f=fopen(adbpath,"a");
		if(f != NULL) writeoutticket(f,tickets[t]);
		if(f != NULL && !fclose(f)){
			delticket(t);
		} else {
			printf("Failed to archive ticket, it has not been deleted from %s, please check permissions.\n",dbpath);
		}

	} else {printf("No such ticket.\n");exit(-1);}
}
void wontticket(int argc,char **argv){
	if(argc<1){printf("USAGE: wont ticket \n Mark ticket as wontdo and move ticket to %s\n",adbpath); exit(-1);}
	int t=indexforname(argv[0]);
	tickets[t].state=WONT;
	tickets[t].ctime=time(NULL);
	if(t>0){
		FILE *f=fopen(adbpath,"a");
		if(f != NULL) writeoutticket(f,tickets[t]);
		if(f != NULL && !fclose(f)){
			delticket(t);
		} else {
			printf("Failed to archive ticket, it has not been deleted from %s, please check permissions.\n",dbpath);
		}

	} else {printf("No such ticket.\n");exit(-1);}
}
void newscrum(int argc, char **argv){
	printf("TODO");
}
void todo(int argc,char **argv){
	if(argc<1) {usage(); exit(1);}
	if(!strcmp(argv[0],"workflow")){workflow();exit(0);}
	if(!strcmp(argv[0],"check")){exit(0);}
	if(!strcmp(argv[0],"stats")){stats();exit(0);}
	else if(!strcmp(argv[0],"normalize")){savedb=1;}
	else if(!strcmp(argv[0],"create")){newticket(argc-1,argv+1);savedb=1;}
	else if(!strcmp(argv[0],"assign")){assign(argc-1,argv+1);savedb=1;}
	else if(!strcmp(argv[0],"do")){doticket(argc-1,argv+1);savedb=1;}
	else if(!strcmp(argv[0],"close")){closeticket(argc-1,argv+1);savedb=1;}
	else if(!strcmp(argv[0],"wont")){wontticket(argc-1,argv+1);savedb=1;}
	else if(!strcmp(argv[0],"import")){readintickets(stdin);savedb=1;}
	else if(!strcmp(argv[0],"show")){showticket(argc-1,argv+1);}
	else if(!strcmp(argv[0],"newscrum")){newscrum(argc-1,argv+1);savedb=1;}
	else if(!strcmp(argv[0],"kanban")){report(argc-1,argv+1,1);}
	else if(!strcmp(argv[0],"report")){report(argc-1,argv+1,0);}
	else if(!strcmp(argv[0],"comment")){comment(argc-1,argv+1);savedb=1;}
	else if(!strcmp(argv[0],"archive")){archive(argc-1,argv+1);savedb=1;}
	else {usage();exit(1);}
}
int main(int argc, char **argv){
	dbpath="./todo.ini";
	adbpath="./todo.old.ini";
	if(getenv("TTDB")!=NULL) dbpath=strdup(getenv("TTDB"));
	if(getenv("TTADB")!=NULL) adbpath=strdup(getenv("TTADB"));
	FILE *f=fopen(dbpath,"r");
	if(f!=NULL){
		readintickets(f);
		todo(argc-1,argv+1);
		fclose(f);
		if(savedb){
			FILE *f=fopen(dbpath,"w");
			if(f!=NULL){
				writeoutdb(f);
			}else{printf("Could not open database for writting\n");exit(-3);}
		}
	} else {
		printf("Please create an empty file at %s. This will be used as the ticket database.\n",dbpath);
	}
	return 0;
}
