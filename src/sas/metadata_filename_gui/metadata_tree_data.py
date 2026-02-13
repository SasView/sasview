#!/usr/bin/env python

# TODO: This file can probably be deleted. Just want to make sure nothing else
# depends on it.

metadata = {
    'source': ['name', 'radiation', 'type', 'probe_particle', 'beam_size_name', 'beam_size', 'beam_shape', 'wavelength', 'wavelength_min', 'wavelength_max', 'wavelength_spread'],
    'detector': ['name', 'distance', 'offset', 'orientation', 'beam_center', 'pixel_size', 'slit_length'],
    'aperture': ['name', 'type', 'size_name', 'size', 'distance'],
    'collimation': ['name', 'lengths'],
    'process': ['name', 'date', 'description', 'term', 'notes'],
    'sample': ['name', 'sample_id', 'thickness', 'transmission', 'temperature', 'position', 'orientation', 'details'],
    'transmission_spectrum': ['name', 'timestamp', 'transmission', 'transmission_deviation'],
    'other': ['title', 'run', 'definition']
}

initial_metadata_dict = {key: {} for key, _ in metadata.items()}
