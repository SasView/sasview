#ifndef bsl_loader_h
#define bsl_loader_h

typedef struct {
    // File to load
    char *filename;
    // Number of frames in the file
    int n_frames;
    // Frame to load
    int frame;
    // Number of pixels in the file
    int n_pixels;
    // Number of rasters in the file
    int n_rasters;
    // Whether or not the bytes are in reverse order
    int swap_bytes;
} CLoader_params;

#endif
