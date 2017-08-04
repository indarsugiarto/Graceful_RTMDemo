#include "chipFwdr.h"

void c_main()
{
    if(initApp()==SUCCESS) {    // check if we're in right chip and core
        if(coreID==LEAD_CORE){
            initRouter();
            initIPtag(0,0);
        }
        initHandlers();
        spin1_start(SYNC_NOWAIT);
    }
}

