#ifndef CHIPFWDR_H
#define CHIPFWDR_H

#include <spin1_api.h>

#include "../vidPro.h"

#define DEBUG_LEVEL 1

#define LEAD_CORE 2

#define PRIORITY_DMA        -1
#define PRIORITY_SDP        0
#define PRIORITY_MCPL       1
#define PRIORITY_FRPL       2
#define PRIORITY_LOW        3

/* SDP-related functionalities */
#define SDP_IMG_INFO_PORT   1
#define SDP_RGB_DATA_PORT   2
#define SDP_EOF_DATA_PORT   3
#define SDP_INTERNAL_PORT   7

#define SDP_RESULT_IPTAG    1
#define SDP_RESULT_PORT     20001

/* Initialization */
uint initRouter();
uint initApp();         // includes sanity check
void initHandlers();
void initIPtag(uint phase, uint hostIP);
void initImgBuf(uint create_or_del, uint arg2);

/* Event handler */
void hSDP (uint mBox, uint port);
void hMCPL(uint key, uint payload);
void hDMA (uint tid, uint tag);
void hFRPL(uint key, uint payload);

/* Variables */
uchar selCore;
frame_info_t frameInfo;
uint imgBufInitialized;
uchar *imgBufIn;
uchar *imgBufOut;
uint coreID;

#endif
