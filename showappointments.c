#define _XOPEN_SOURCE 500
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <string.h>
#define DLINE
//#define DLINE //
#define DBUG(x) DLINE printf("x\n");

time_t timeof(char *line) {
		struct tm cur = {};
		char *ltemp=strdup(line);
		char *dates = strtok(ltemp,"-");
		if (strptime(dates, "%b %d, %Y %R %p", &cur) == NULL) {
		if (strptime(dates, "%b %d, %Y %R", &cur) == NULL) {
		if (strptime(dates, "%b %d, %Y", &cur) == NULL) {
		if (strptime(dates, "%b %d %R", &cur) == NULL) {
		if (strptime(dates, "%b %d %R %p", &cur) == NULL) {
		if (strptime(dates, "%b %d", &cur) == NULL) {
		if (strptime(dates, "%a", &cur) == NULL) {
					printf("Error: could not parse date string %s\n",dates);
					return -1;
		}}}}}}} //This is shockingly ugly.
		char ts[256];
		time_t timestamp = mktime(&cur);
		free(ltemp);
		return timestamp;
}

void showfor(FILE *fp, time_t cutoff) {
	char line[256];
	if (fseek(fp, 0, SEEK_SET) != 0) {
		printf("Error: could not seek to beginning of file\n");
	}
	time_t now = time(NULL);
	while (fgets(line, sizeof(line), fp)) {
		if(line[0] == '#')
			continue; //skip commented lines
		// Parse the date and time from the beginning of the line
		time_t timestamp=timeof(line);
		// Check if the appointment is within the cutoff time
		if (timestamp == -1) {
			printf("Error: could not convert date to timestamp\n");
			continue;
		}
		if (timestamp <= cutoff && timestamp >= now - 86400) {
			printf("%s\n",line);
		}
	}
}
int show(void) {
	time_t now = time(NULL);
	FILE* fp = fopen("/home/swiley/stuff/appointments", "r");
	if (fp == NULL) {
		printf("Error: could not open file\n");
		return 1;
	}
	puts("====   Appointments today:   ====");
	showfor(fp,now + 86400);
	puts("====   Appointments weekly:  ====");
	showfor(fp,now + 86400*7);
	puts("====   Appointments monthly: ====");
	showfor(fp,now + 86400*30);
	fclose(fp);
	return 0;
}
int import(void) {
}
int export(char *line) {
}
int main(int argc, char *argv[]) {
	if(argc==1) return show();
	else if(argc==2 && !strcmp("show",argv[1])) return show();
	else if(argc==2 && !strcmp("import",argv[1])) return import();
	else if(argc==3 && !strcmp("export",argv[1])) return export(argv[2]);
	else printf("Usage: %s [show|import|export appointment]\n",argv[0]);
	return 2;
}
