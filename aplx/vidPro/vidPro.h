#ifndef VIDPRO_H
#define VIDPRO_H

/* This is common header that will be used by all sub-programs. */


// Predefined image processing
#define IMG_OP_SOBEL_NO_FILT            1	// will be carried in arg2.low
#define IMG_OP_SOBEL_WITH_FILT          2	// will be carried in arg2.low
#define IMG_OP_LAP_NO_FILT              3	// will be carried in arg2.low
#define IMG_OP_LAP_WITH_FILT            4	// will be carried in arg2.low
#define IMG_NO_FILTERING                0
#define IMG_WITH_FILTERING              1
#define IMG_SOBEL                       0
#define IMG_LAPLACE                     1


typedef struct frame_info {
    unsigned short int wImg;
    unsigned short int hImg;
    unsigned int szPixmap;              // pixel size as wImg x hImg
    unsigned char isGrey;			// 0==color, 1==gray
    unsigned char opType;			// 0==sobel, 1==laplace
    unsigned char opFilter;			// 0==no filtering, 1==with filtering
} frame_info_t;

#endif
