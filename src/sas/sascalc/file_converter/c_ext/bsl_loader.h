#ifndef bsl_loader_h
#define bsl_loader_h

typedef struct {
    // File to load
    char *filename;
    // Frame to load
    int frame;
    // Number of pixels in the file
    int n_pixels;
    // Number of rasters in the file
    int n_rasters;
} CLoader_params;

#endif
