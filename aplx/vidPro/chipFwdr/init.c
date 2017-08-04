#include "chipFwdr.h"

// iptag
// IPTAG definitions from scamp:
#define IPTAG_NEW		0
#define IPTAG_SET		1
#define IPTAG_GET		2
#define IPTAG_CLR		3
#define IPTAG_TTO		4

sdp_msg_t iptag;
/* initIPtag() should be executed by leadAp. There are three phases:
 * phase-0: will be called by c_main to init iptag and schedule it
 * phase-1: will send IPTAG_GET to collect host IP address
 * phase-2: will set iptag
 * */
void initIPtag(uint phase, uint hostIP)
{
    if(phase==0) {
        // prepare sdp container for iptag
        iptag.flags = 0x87;	// initially needed for iptag triggering
        iptag.tag = 0;		// internal
        iptag.srce_addr = sv->p2p_addr;
        iptag.srce_port = (SDP_INTERNAL_PORT << 5) + (uchar)coreID;	// use port-7
        iptag.dest_addr = sv->p2p_addr;
        iptag.dest_port = 0;				// send to "root" (scamp)
        iptag.cmd_rc = CMD_IPTAG;
        iptag.arg1 = (IPTAG_GET << 16) + 0; // target iptag-0
        iptag.arg2 = 1; //remember, scamp use this for some reason
        iptag.length = sizeof(sdp_hdr_t) + sizeof(cmd_hdr_t);
        spin1_schedule_callback(initIPtag, 1, 0, PRIORITY_LOW);
    }
    else if(phase==1) {
        spin1_send_sdp_msg(&iptag, 10);
    }
    else if(phase==2) {
        iptag.flags = 7;
        iptag.arg1 = (IPTAG_SET << 16) + SDP_RESULT_IPTAG;
        iptag.arg2 = SDP_RESULT_PORT;
        iptag.arg3 = hostIP;
        spin1_send_sdp_msg(&iptag, 10);
    }
}

uint initApp()
{
    uint ok;
    coreID = sark_core_id();
    if(sv->p2p_addr!=0 || coreID<2) {
#if(DEBUG_LEVEL>0)
        io_printf(IO_STD, "[ERR] Wrong core/chip!\n");
#endif
        ok = FAILURE;
    }
    else {
        imgBufInitialized = FALSE;
        imgBufIn = NULL;
        imgBufOut = NULL;

        selCore = coreID; // will be used by leadAp, initially point to itself
    }

    return ok;
}

/* initRouter() should be done only by leadAp
 * */
uint initRouter()
{
    uint ok;

    return ok;
}

void initHandlers()
{
    spin1_callback_on(MCPL_PACKET_RECEIVED, hMCPL, PRIORITY_MCPL);
    spin1_callback_on(SDP_PACKET_RX, hSDP, PRIORITY_SDP);
    spin1_callback_on(DMA_TRANSFER_DONE, hDMA, PRIORITY_DMA);
    spin1_callback_on(FRPL_PACKET_RECEIVED, hFRPL, PRIORITY_FRPL);
}

// create_or_del 0 -> create, 1 -> free
void initImgBuf(uint create_or_del, uint arg2)
{
    if(create_or_del==0) {
        // resize image buffer if necessary
        if(imgBufInitialized==TRUE){
            sark_xfree(sv->sdram_heap, imgBufIn, ALLOC_LOCK);
            sark_xfree(sv->sdram_heap, imgBufOut, ALLOC_LOCK);
        }
        imgBufIn = sark_xalloc(sv->sdram_heap, frameInfo.szPixmap, 0, ALLOC_LOCK);
        imgBufOut = sark_xalloc(sv->sdram_heap, frameInfo.szPixmap, 0, ALLOC_LOCK);
        if(imgBufIn==NULL || imgBufOut==NULL) {
            rt_error(RTE_MALLOC);
#if(DEBUG_LEVEL>0)
            io_printf(IO_STD, "[ERR] Cannot allocate image buffers!\n");
#endif
        }
        else {
            imgBufInitialized=TRUE;
        }
    }
    else {
        sark_xfree(sv->sdram_heap, imgBufIn, ALLOC_LOCK);
        sark_xfree(sv->sdram_heap, imgBufOut, ALLOC_LOCK);
        imgBufInitialized=FALSE;
    }
}

