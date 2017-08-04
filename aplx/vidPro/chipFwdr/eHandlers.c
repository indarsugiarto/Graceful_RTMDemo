#include "chipFwdr.h"

static void getImgInfoAndFwd(sdp_msg_t *msg);
static void dispatchRGBdata(sdp_msg_t *msg);
static void getRGBdata(sdp_msg_t *msg);

void hSDP(uint mBox, uint port)
{
    sdp_msg_t *msg = (sdp_msg_t *)mBox;
    uint rm_msg = TRUE;    // should remove msg here?

    // in the beginning, host should tell us the size of a frame
    if(port==SDP_IMG_INFO_PORT) {
        getImgInfoAndFwd(msg);
    }
    else if(port==SDP_RGB_DATA_PORT) {
        dispatchRGBdata(msg);
        rm_msg=FALSE;
    }
    else if(port==SDP_EOF_DATA_PORT) {

    }
    else if(port==SDP_INTERNAL_PORT) {
        // if receiving "OK" from scamp
        if(msg->cmd_rc==0x80) {
            spin1_schedule_callback(initIPtag, 2, msg->arg1, PRIORITY_LOW);
        }
    }

    if(rm_msg==TRUE) {
        spin1_msg_free(msg);
    }
}

void hMCPL(uint key, uint payload)
{

}

void hDMA(uint tid, uint tag)
{

}

void hFRPL(uint key, uint payload)
{

}


/*------------------ Functions implementation ------------------*/
void getImgInfoAndFwd(sdp_msg_t *msg)
{
    // forward this information to chip <2,2> as well
    msg->dest_addr = 0x202;
    spin1_send_sdp_msg(msg, 10);

    // and collect info for internal purpose
    frameInfo.wImg = msg->arg1 >> 16;
    frameInfo.hImg = msg->arg1 & 0xFFFF;
    frameInfo.isGrey = msg->seq >> 8;
    frameInfo.szPixmap = frameInfo.wImg * frameInfo.hImg;
    if(frameInfo.isGrey==0)
        frameInfo.szPixmap *= 3;
    switch(msg->seq & 0xFF) {
    case IMG_OP_SOBEL_NO_FILT:
        frameInfo.opFilter = IMG_NO_FILTERING; frameInfo.opType = IMG_SOBEL; break;
    case IMG_OP_SOBEL_WITH_FILT:
        frameInfo.opFilter = IMG_WITH_FILTERING; frameInfo.opType = IMG_SOBEL; break;
    case IMG_OP_LAP_NO_FILT:
        frameInfo.opFilter = IMG_NO_FILTERING; frameInfo.opType = IMG_LAPLACE; break;
    case IMG_OP_LAP_WITH_FILT:
        frameInfo.opFilter = IMG_WITH_FILTERING; frameInfo.opType = IMG_LAPLACE; break;
    }
    // then schedule for image buffer creation
    spin1_schedule_callback(initImgBuf, 0, 0, PRIORITY_LOW);
}

static void dispatchRGBdata(sdp_msg_t *msg)
{
    if(selCore==coreID) {
        getRGBdata(msg);
    }
}

static void getRGBdata(sdp_msg_t *msg)
{

    spin1_msg_free(msg);
}
