//Kanban boards
#define _GNU_SOURCE 2
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <sys/stat.h>
//#define DBLINE //
#define DBLINE 
enum state_t {TODO =1, DOING, DONE,WONT,BACKLOG};
char *state_strings[] = { "INVALID", "TODO","DOING","DONE","WONT","BACKLOG"};
enum type_t {TICKET=1, COMMENT,EPIC};
char *type_strings[] = { "INVALID", "TICKET","EPIC"};
enum swimlane_t {NONE=0, TYPE, WEB};
const int promodorotime=20*60*1000;
#define MAXCOMMENTS 20
#define MAXSUPS 40
#define MAX_TICKETS 10000
typedef struct {
 char *name;
 char *desc;
 char *closemesg;
 char *assignee;
 char *reporter;
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
 char *sups[MAXSUPS];
 int supcount;
 int commentcount;
} ticket;

ticket tickets[MAX_TICKETS];
int lastticket=-1;
int defaultstate=TODO;
int multiusermode=1;
int fortnight=86400*14;
char *dbpath;
char *adbpath;
char *backname=".~TODO";
char *weburl="";
char *upcmd="";
char *cssurl="";
char *vibecmd="";
int defaultpoints=3;
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
	if(!strcasecmp(l,"backup"))backname=val;
	else if(!strcasecmp(l,"upcmd"))upcmd=val;
	else if(!strcasecmp(l,"weburl"))weburl=val;
	else if(!strcasecmp(l,"cssurl"))cssurl=val;
	else if(!strcasecmp(l,"vibecmd"))vibecmd=val;
	else {//free val
		if(!strcasecmp(l,"fortnight"))fortnight=atoi(val);
		else if(!strcasecmp(l,"defaultstate"))defaultstate=atoi(val);
		else if(!strcasecmp(l,"multiusermode"))multiusermode=atoi(val);
		else if(!strcasecmp(l,"defaultpoints"))defaultpoints=atoi(val);
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
	else if(strcasestr(l,"sup")==l){
		if(tickets[t].supcount<MAXCOMMENTS){
			tickets[t].supcount++;
			tickets[t].sups[tickets[t].supcount-1]=val;
		}else{
			error("too many status updates at line",lnum);
		}
	}
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
			else if(!strcasecmp(val,"BACKLOG"))tickets[t].state=BACKLOG;
			else invalidkey(lnum,tickets[t].name,l,val);
		}else if(!strcasecmp(l,"type")){
			if(!strcasecmp(val,"TICKET"))tickets[t].type=TICKET;
			else if(!strcasecmp(val,"EPIC"))tickets[t].type=EPIC;
			else invalidkey(lnum,tickets[t].name,l,val);
		} else if(!strcasecmp(l,"points"))tickets[t].points=atoi(val);
		else if(!strcasecmp(l,"otime"))tickets[t].otime=atoi(val);
		else if(!strcasecmp(l,"dtime"))tickets[t].dtime=atoi(val);
		else if(!strcasecmp(l,"ctime"))tickets[t].ctime=atoi(val);
		else if(!strcasecmp(l,"etime"))tickets[t].etime=atoi(val);
		else if(!strcasecmp(l,"priority"))tickets[t].priority=atoi(val);
		else{invalidkey(lnum,tickets[t].name,l,val);}
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
void tform(FILE *f, char *name,char *url) {
	fprintf(f,"<form method='POST'>\n");
	fprintf(f,"<input name='section', value='%s', type='hidden'></hidden>\n",name);
}
void writekey(FILE *f, char *name, char *key,char *value, int format) {
	if(format==WEB) {
		tform(f,name,weburl);
		fprintf(f,"%s: <input name='%s' value='%s'> </input>\n",key,key,value);
		fprintf(f,"</form>");
	}else {
		fprintf(f,"%s=%s\n",key,value);
	}
}
void writelong(FILE *f, char *name, char *key,long int value, int format) {
	if(format==WEB) {
		tform(f,name,weburl);
		fprintf(f,"%s: <input name='%s' value='%ld'> </input>\n",key,key,value);
		fprintf(f,"</form>");
	}else {
		fprintf(f,"%s=%ld\n",key,value);
	}
}
void writeoutticket(FILE *f,ticket t,int format){
	if(format==WEB)
		fprintf(f,"<h1>%s</h1>\n",t.name);
	else
		fprintf(f,"[%s]\n",t.name);
	writekey(f,t.name,"desc", t.desc, format);
	if(t.assignee!=NULL) writekey(f,t.name,"assignee",t.assignee,format);
	if(t.reporter!=NULL) writekey(f,t.name,"reporter",t.reporter,format);
	writekey(f,t.name,"state",state_strings[t.state],format);
	writekey(f,t.name,"type",type_strings[t.type],format);
	writelong(f,t.name,"points",t.points,format);
	if(t.otime) writelong(f,t.name,"otime",t.otime,format);
	if(t.dtime) writelong(f,t.name,"dtime",t.dtime,format);
	if(t.ctime) writelong(f,t.name,"ctime",t.ctime,format);
	if(t.etime) writelong(f,t.name,"etime",t.etime,format);
	for(int i=0;i<t.commentcount ;i++){
		writekey(f,t.name,"%s",t.comments[i],format);
	}
	for(int i=0;i<t.supcount ;i++){
		char buf[255];
		snprintf(buf,sizeof(char)*255,"sup%d",i+1);
		writekey(f,t.name,buf,t.sups[i],format);
	}
}
void writeoutdb(FILE *f) {
	int tcount=0;
	fprintf(f,"#autogenerated from tt\nmultiusermode=%d\ndefaultstate=%d\n",multiusermode,defaultstate);
	fprintf(f,"backup=%s\ndefaultpoints=%d\n",backname,defaultpoints);
	if(strlen(weburl)) fprintf(f,"weburl=%s\n",weburl);
	if(strlen(upcmd)) fprintf(f,"upcmd=%s\n",upcmd);
	if(strlen(cssurl)) fprintf(f,"cssurl=%s\n",cssurl);
	if(strlen(vibecmd)) fprintf(f,"vibecmd=%s\n",vibecmd);
	for(int i=0;i<=lastticket;i++){
		if(!tickets[i].ephemeral){
			tcount++;
			writeoutticket(f,tickets[i],NONE);
			fflush(f);
		}
	}
	printf("%d tickets written to database.\n",tcount);
}
void workflow(void) {
	printf("In kanban mode you should create a ticket as soon as a bug or unit of work is discovered. Before assigning it to a worker, a number of relative \"points\" should be added as an intuitive measure of how difficult the ticket appears. This can help judge the health of the team and help other people make predictions for future work.\n");
	printf("It's recommended that workers provide a daily status update for tickets using the sup command.\n");
	printf("Each day someone (likely a manager/emcee/'scrummaster') should run the kanban command and go through the tickets in the doing column for status updates to discover blocking problems and share advice. The report command may be used periodically to judge organizational effectiveness.\n");
	printf("Tickets outside the current scope should be put in the BACKLOG state to keep them out of reports.\n");
	printf("When used with a feature branch worklow on a VCS, branches should be named after the ticket. This way they can be found by running `git branch | grep ticketname`.\n");
	printf("TT will not manage database history for you, a VCS tool like git is recommended for this.\n\n");
	printf("Useful automations:\n");
}
void usage(void){
	printf("tt tracks tickets in an INI formated databse at $TTDB or ./todo.ini\n");
	printf("USAGE: tt subcmd ticket [message]\n");
	printf("subcommand list:\n");
	printf(" check: load database and report errors\n");
	printf(" normalize: check database and write it back\n");
	printf(" create: create the specified ticket with the default state and $USER as reporter\n");
	printf(" todo: create or move the specified ticket in TODO with $USER as reporter\n");
	printf(" backlog: create or move the specified ticket in BACKLOG with $USER as reporter\n");
	printf(" assign: assign the specified ticket to assignee with points\n");
	printf(" do: move  the specified ticket to doing column\n");
	printf(" close: close the specified ticket with message as close message\n");
	printf(" show: write ticket to stdout\n");
	printf(" import: read tickets from stdin, overwritting data in db (missing data will merge, so you can run show followed by import and enter new values for the fields this way.)\n");
	printf(" kanban: show ticket summaries in swimlanes, tickets outside scope will be hidden.\n");
	printf(" report: write out historical report for tickets one per line.\n"); 
	printf(" stats: write out statistics report for current tickets.\n"); 
	printf(" vibecode: delegate a ticket to the language model in ~/models/coder.gguf and have it write a patch (this requires llama-cli in your path.)\n");
	printf(" genvibecmd: generate a vibecmd script for use with vibecode and update vibecmd setting.\n");
	printf(" archive: move ticket to todo.old.ini.\n");
	printf(" workflow: advice on using tt in your workflow.\n");
	printf(" sup: Add a status update to ticket.\n");
	printf(" promodoro: start a timer to work on a ticket and log one period to .promodoro.punches\n");
	printf(" dayscope: Mark a ticket as worked on today by appending it to .day.punches with a timestamp.\n");
	printf("\n");
}
void newticket(int argc, char **argv, int state) {
	char name[500];
	char desc[500];
	if(argc<1){
		printf("The name of the ticket is the primary key.\nname: ");
		fgets(name,500,stdin);
		name[strlen(name)-1]='\0';
	}else{strcpy(name,argv[0]);}
	if(indexforname(name)>0||!strcmp(name,"global")){
		if(state==0) {printf("name already in use.\n");exit(-1);}
		else {
			tickets[indexforname(name)].state=state;
			return;
		}
	}
	if(state==0) state=defaultstate;
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
	tickets[lastticket].state=state;
	tickets[lastticket].type=TICKET;
	tickets[lastticket].points=defaultpoints;
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
			printf("The assignee will be responsible for completing the specified work unit.\nassignee: ");
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
	if(t>=0){
		tickets[t].state=DONE;
		tickets[t].ctime=time(NULL);
	} else printf("No such ticket.\n");
}
void reportswimlane(ticket t, int swimlane){
	if(t.state==BACKLOG || t.state==WONT || t.state==0) return;
	if(swimlane==WEB) printf("<tr>");
	for(int i=TODO;i<t.state;i++){
		if(swimlane==TYPE) printf("\t\t\t\t");
		if(swimlane==WEB) printf("<td></td>");
	}
	if(swimlane == WEB) printf("<td>");
	if(multiusermode) printf("[%s @ %s : %d]\n",t.name,t.assignee,t.points);
	if(!multiusermode) printf("[%s : %d]",t.name,t.points);
	if(swimlane == WEB) {
		printf("<br>");
		if(strlen(weburl)){
			tform(stdout,t.name,weburl);
			if(t.state>TODO)
				printf("<button class='la' name='%s'><-</button>",state_strings[t.state+1]);
			if(t.state<DONE)
				printf("<button class='ra' name='%s'>-></button>",state_strings[t.state-1]);
			printf("</form><br>\n");
			printf("<a href='%s/%s'>Details</a>",weburl,t.name);
		}
	}
	if(t.supcount && t.state != DONE){
		char *status=t.sups[t.supcount-1];
		if(status!=NULL&&strlen(status)>0) printf(" (%s)", status);
	}
	if(swimlane == WEB) printf("</td></tr>\n");
	else printf("\n");
}
void reportone(ticket t){
	if(t.state==BACKLOG || t.state==WONT || t.state==0) return;
	printf("%s\t%d\t%ld\t%ld\n",t.assignee,t.points,t.ctime-t.otime,t.ctime-t.dtime);
}
void webheader(int board) {
	printf("<html><head><title>Kanban Board</title></head>\n");
	if(strlen(cssurl)) printf("<link meta=css url='%s'></link>",cssurl);
	else{
		printf("<style>\n");
		printf("td: border=black;\n");
		printf("</style>\n");
	}
	if(board){
		printf("<body><h1>Kanban Board</h1><hr><div id='board'><table>\n");
		printf("<tr><th>TODO</th><th>DOING</th><th>DONE</th>\n");
	}else{
		printf("<body>\n");
	}
}
void webfooter(int board) {
	if(board) printf("</div></table></body></html>\n");
	else printf("</body></html>\n");
}
void report(int argc, char **argv,int swimlane){
	if(swimlane == TYPE ) printf("TODO\t\t\t\tDOING\t\t\t\tDONE\n");
	else if(swimlane == WEB) webheader(1);
	else printf("ASIGNEE\tPOINTS\tTIMEOPEN\tTIMEDOING\n");
	for(int i=0;i<=lastticket;i++){
		if(swimlane == TYPE || swimlane == WEB) reportswimlane(tickets[i],swimlane);
		else reportone(tickets[i]);
	}
	if(swimlane == WEB) webfooter(1);
}
void showticket(int argc, char **argv, int format){
	if(argc<1){printf("USAGE: show ticket\n Export ticket to stdout.\n"); exit(-1);}
	int t=indexforname(argv[0]);
	if(t>=0){
		writeoutticket(stdout,tickets[t],format);
	} else printf("No such ticket.\n");
}
void webdetail(ticket t){
	webheader(0);
	showticket(1,&t.name,WEB);
	webfooter(0);
}
void stats(int argc, char **argv){ //TODO: allow statistics to be reported over sliding time window.
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
	if(!(argc>=1 && !strcmp(argv[0],"noheader")))
		printf("toclose\ttodoing\tavg age\topen\tdoing\tdone\ttotal\t\t Time in hours.\n");
	printf("%lld\t%lld\t%lld\t%d\t%d\t%d\t%d\n",catimetoclose/timediv,catimedoing/timediv,caage/timediv,opencount,doingcount,donecount,totalcount);
}
void comment(int argc,char **argv){
	if(argc<1){printf("USAGE: comment ticket \"comment\"\n add a short comment to a ticket.\n"); exit(-1);}
	int t=indexforname(argv[0]);
	if(t>=0){
		if( tickets[t].commentcount<MAXCOMMENTS){
			tickets[t].commentcount++;
			tickets[t].comments[tickets[t].commentcount-1]=strdup(argv[1]);
		}else { printf("Too many comments already.\n");exit(-2);}
	} else {printf("No such ticket.\n");exit(-1);}
}
void promodoro(int argc,char **argv){
	if(argc<1){printf("USAGE: promodoro ticket\n Work ticket for promodoro period and log to .prmodoro.punches.\n"); exit(-1);}
	int t=indexforname(argv[0]);
	if(t>=0){
		printf("Work for 20 minutes...");
		usleep(promodorotime);
		printf("punching...");
		FILE *f=fopen(".prmodoro.punches","a");
		if(f != NULL) {
			fprintf(f,"%s\n",argv[1]);
		}else{
			printf("Failed to punch in.\n");
		}
	} else {printf("No such ticket.\n");exit(-1);}
}
void dayscope(int argc,char **argv){
	if(argc<1){printf("USAGE: dayscope ticket\n Work ticket for 24h period and log to .day.punches.\n"); exit(-1);}
	int t=indexforname(argv[0]);
	if(t>=0){
		FILE *f=fopen(".day.punches","a");
		if(f != NULL) {
			fprintf(f,"%ld %s\n",(long)time(NULL),argv[0]);
		}else{
			printf("Failed to punch in.\n");
		}
	} else {printf("No such ticket.\n");exit(-1);}
}
void vibecode(int argc,char **argv){
	if(argc<2){printf("USAGE: vibecode ticket\nDelegate ticket to AI \"vibecmd\".\n"); exit(-1);}
	int t=indexforname(argv[0]);
	if(t>=0){
		if(strlen(vibecmd)){
			char *tempcmd;
			if(asprintf(&tempcmd,"%s %s",vibecmd,tickets[t].desc)){
				if(!system(tempcmd)) {
					printf("AI completed.\n");
				}else{
					printf("AI vibecmd failed.\n");
					exit(1);
				}
			}else {
				printf("alloc failed\n");
			}
			free(tempcmd);
		}else {
			printf("You must configure a vibecoder script under the global \"vibecmd\" key in todo.ini.\n");
			exit(1);
		}
	} else {printf("No such ticket.\n");exit(-1);}
}
void genvibecmd(int argc, char **argv){
	const char *script_path = "./vibecoder.sh";
	const char *script_content =
		"#!/bin/bash\n"
		"# vibecoder.sh: Script to process ticket description with llama-cli\n"
		"if [ $# -lt 1 ]; then\n"
		"    echo \"Usage: $0 <ticket_description>\"\n"
		"    exit 1\n"
		"fi\n"
		"DESCRIPTION=\"$1\"\n"
		"llama-cli -m ~/models/coder.gguf -p \"Generate a patch for: $DESCRIPTION\" > patch.out\n"
		"if [ $? -eq 0 ]; then\n"
		"    echo \"Patch generated in patch.out\"\n"
		"    exit 0\n"
		"else\n"
		"    echo \"Failed to generate patch\"\n"
		"    exit 1\n"
		"fi\n";
	
	FILE *f = fopen(script_path, "w");
	if (f == NULL) {
		printf("Failed to create vibecmd script at %s\n", script_path);
		exit(-1);
	}
	fprintf(f, "%s", script_content);
	fclose(f);
	
	if (chmod(script_path, S_IRWXU) != 0) {
		printf("Failed to set executable permissions on %s\n", script_path);
		exit(-1);
	}
	
	vibecmd = strdup(script_path);
	savedb = 1;
	
	printf("Generated vibecmd script at %s and updated vibecmd setting.\n", script_path);
}
void archive(int argc,char **argv){
	if(argc<1){printf("USAGE: archive ticket \n Move ticket to %s\n",adbpath); exit(-1);}
	int t=indexforname(argv[0]);
	if(t>=0){
		FILE *f=fopen(adbpath,"a");
		if(f != NULL) writeoutticket(f,tickets[t],NONE);
		if(f != NULL && !fclose(f)){
			delticket(t);
		} else {
			printf("Failed to archive ticket, it has not been deleted from %s, please check permissions.\n",dbpath);
		}
	} else {printf("No such ticket.\n");exit(-1);}
}
void sup(int argc,char **argv){
	if(argc<2){printf("USAGE: sup ticket \"sup\"\n Create a status update.\n"); exit(-1);}
	int t=indexforname(argv[0]);
	if(t>=0){
		if( tickets[t].supcount<MAXSUPS){
			tickets[t].supcount++;
			tickets[t].sups[tickets[t].supcount-1]=strdup(argv[1]);
		}else { printf("Too many sups already.\n");exit(-2);}
	} else {printf("No such ticket.\n");exit(-1);}
}
void wontticket(int argc,char **argv){
	if(argc<1){printf("USAGE: wont ticket \n Mark ticket as wontdo and move ticket to %s\n",adbpath); exit(-1);}
	int t=indexforname(argv[0]);
	tickets[t].state=WONT;
	tickets[t].ctime=time(NULL);
	if(t>=0){
		FILE *f=fopen(adbpath,"a");
		if(f != NULL) writeoutticket(f,tickets[t],NONE);
		if(f != NULL && !fclose(f)){
			delticket(t);
		} else {
			printf("Failed to archive ticket, it has not been deleted from %s, please check permissions.\n",dbpath);
		}
	} else {printf("No such ticket.\n");exit(-1);}
}
void todo(int argc,char **argv){
	if(argc<1) {usage(); exit(1);}
	if(!strcmp(argv[0],"workflow")){workflow();exit(0);}
	if(!strcmp(argv[0],"check")){exit(0);}
	if(!strcmp(argv[0],"stats")){stats(argc-1,argv+1);exit(0);}
	else if(!strcmp(argv[0],"normalize")){savedb=1;}
	else if(!strcmp(argv[0],"create")){newticket(argc-1,argv+1,0);savedb=1;}
	else if(!strcmp(argv[0],"todo")){newticket(argc-1,argv+1,TODO);savedb=1;}
	else if(!strcmp(argv[0],"backlog")){newticket(argc-1,argv+1,BACKLOG);savedb=1;}
	else if(!strcmp(argv[0],"assign")){assign(argc-1,argv+1);savedb=1;}
	else if(!strcmp(argv[0],"do")){doticket(argc-1,argv+1);savedb=1;}
	else if(!strcmp(argv[0],"close")){closeticket(argc-1,argv+1);savedb=1;}
	else if(!strcmp(argv[0],"wont")){wontticket(argc-1,argv+1);savedb=1;}
	else if(!strcmp(argv[0],"import")){readintickets(stdin);savedb=1;}
	else if(!strcmp(argv[0],"show")){showticket(argc-1,argv+1,TYPE);}
	else if(!strcmp(argv[0],"webshow")){showticket(argc-1,argv+1,WEB);}
	else if(!strcmp(argv[0],"kanban")){report(argc-1,argv+1,TYPE);}
	else if(!strcmp(argv[0],"webkanban")){report(argc-1,argv+1,WEB);}
	else if(!strcmp(argv[0],"report")){report(argc-1,argv+1,NONE);}
	else if(!strcmp(argv[0],"comment")){comment(argc-1,argv+1);savedb=1;}
	else if(!strcmp(argv[0],"sup")){sup(argc-1,argv+1);savedb=1;}
	else if(!strcmp(argv[0],"promodoro")){sup(argc-1,argv+1);savedb=0;}
	else if(!strcmp(argv[0],"dayscope")){dayscope(argc-1,argv+1);savedb=0;}
	else if(!strcmp(argv[0],"archive")){archive(argc-1,argv+1);savedb=1;}
	else if(!strcmp(argv[0],"vibecode")){vibecode(argc-1,argv+1);savedb=1;}
	else if(!strcmp(argv[0],"genvibecmd")){genvibecmd(argc-1,argv+1);exit(0);}
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
			rename(dbpath,backname);
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
