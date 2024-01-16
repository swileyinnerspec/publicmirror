#define _XOPEN_SOURCE 500
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <string.h>
#define DLINE
//#define DLINE //
#define DBUG(x) DLINE printf("x\n");

void showfor(FILE *fp, time_t cutoff) {
	char line[256];
	if (fseek(fp, 0, SEEK_SET) != 0) {
		printf("Error: could not seek to beginning of file\n");
	}
	time_t now = time(NULL);
	struct tm cur;
	while (fgets(line, sizeof(line), fp)) {
		if(line[0] == '#')
			continue; //skip commented lines
		// Parse the date and time from the beginning of the line
		struct tm *tm;
//		tm->tm_year = cur->tm_year;
//		tm->tm_mon= cur->tm_mon;
		char *dates = strtok(strdup(line),"-");//XXX This needs to be cleaned up
		if (strptime(dates, "%b %d, %Y %R %p", &cur) == NULL) {
		if (strptime(dates, "%b %d, %Y %R", &cur) == NULL) {
		if (strptime(dates, "%b %d, %Y", &cur) == NULL) {
		if (strptime(dates, "%b %d %R", &cur) == NULL) {
		if (strptime(dates, "%b %d %R %p", &cur) == NULL) {
		if (strptime(dates, "%b %d", &cur) == NULL) {
		if (strptime(dates, "%a", &cur) == NULL) {
					printf("Error: could not parse date string %s\n",dates);
					continue;
		}}}}}}}
		char ts[256];
		time_t timestamp = mktime(&cur);
		if (timestamp == -1) {
			printf("Error: could not convert date to timestamp\n");
			continue;
		}
		// Check if the appointment is within the cutoff time
		if (timestamp <= cutoff && timestamp >= now) {
			printf("%s\n",line);
		}
		free(dates);
	}
}
int main() {
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
