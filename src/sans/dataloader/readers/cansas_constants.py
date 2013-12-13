## Left off at SASInstrument, line 178

class cansasConstants:
    CANSAS_NS = {
                 "1.0" : {
                          "ns" : "cansas1d/1.0", 
                          "schema" : "cansas1d_v1_0.xsd"
                          },
                 "1.1" : {
                          "ns" : "urn:cansas1d:1.1", 
                          "schema" : "cansas1d_v1_1.xsd"
                          }
                 }
    CANSAS_FORMAT = {
                     "SASentry" : {
                                   "units_optional" : True,
                                   "variable" : " ",
                                   "storeas" : "content",
                                   "attributes" : {"name" : {"variable" : "{0}.run_name[node_value] = \"{1}\""}},
                                   "children" : {
                                                 "Title" : {"variable" : "{0}.title = \"{1}\""},
                                                 "Run" : {
                                                          "variable" : "{0}.run.append(\"{1}\")",
                                                          "attributes" : {"name" : {"variable" : "{0}.run_name[node_value] = \"{1}\""}}
                                                          },
                                                 "SASdata" : {
                                                              "attributes" : {"name" : {"variable" : "{0}.meta_data[\"{2}\"] = \"{1}\"",}},
                                                              "children" : {"Idata" : {
                                                                                       "storeas" : "float",
                                                                                       "variable" : None,
                                                                                       "units_optional" : False,
                                                                                       "attributes" : {
                                                                                                       "name" : {
                                                                                                                 "variable" : "{0}.meta_data[\"{2}\"] = \"{1}\"",
                                                                                                                 "storeas" : "content",
                                                                                                                 },
                                                                                                       "timestamp" : {
                                                                                                                      "variable" : "{0}.meta_data[\"{2}\"] = \"{1}\"",
                                                                                                                      "storeas" : "content",
                                                                                                                      }
                                                                                                        },
                                                                                       "children" : {
                                                                                                     "Q" : {
                                                                                                            "variable" : "{0}.x = numpy.append({0}.x, {1})",
                                                                                                            "unit" : "_xunit",
                                                                                                            "attributes" : {
                                                                                                                            "unit" : {
                                                                                                                                      "variable" : "{0}._xunit",
                                                                                                                                      "storeas" : "content"
                                                                                                                                      }
                                                                                                                            }
                                                                                                            },
                                                                                                     "I" : {
                                                                                                            "variable" : "{0}.y = numpy.append({0}.y, {1})",
                                                                                                            "unit" : "_yunit",
                                                                                                            "attributes" : {
                                                                                                                            "unit" : {
                                                                                                                                      "variable" : "{0}._yunit",
                                                                                                                                      "storeas" : "content"
                                                                                                                                      }
                                                                                                                            }
                                                                                                            },
                                                                                                     "Idev" : {
                                                                                                               "variable" : "{0}.dy = numpy.append({0}.dy, {1})",
                                                                                                               "attributes" : {
                                                                                                                               "unit" : {
                                                                                                                                         "variable" : "{0}.meta_data[\"{2}\"] = \"{1}\"",
                                                                                                                                         "storeas" : "content"
                                                                                                                                         }
                                                                                                                               },
                                                                                                               },
                                                                                                     "Qdev" : {
                                                                                                               "variable" : "{0}.dx = numpy.append({0}.dx, {1})",
                                                                                                               "attributes" : {
                                                                                                                               "unit" : {
                                                                                                                                         "variable" : "{0}.meta_data[\"{2}\"] = \"{1}\"",
                                                                                                                                         "storeas" : "content"
                                                                                                                                         }
                                                                                                                               },
                                                                                                               },
                                                                                                     "dQw" : {
                                                                                                              "variable" : "{0}.dxw = numpy.append({0}.dxw, {1})",
                                                                                                              "attributes" : {
                                                                                                                              "unit" : {
                                                                                                                                        "variable" : "{0}.meta_data[\"{2}\"] = \"{1}\"",
                                                                                                                                        "storeas" : "content"
                                                                                                                                        }
                                                                                                                              },
                                                                                                              },
                                                                                                     "dQl" : {
                                                                                                              "variable" : "{0}.dxl = numpy.append({0}.dxl, {1})",
                                                                                                              "attributes" : {
                                                                                                                              "unit" : {
                                                                                                                                        "variable" : "{0}.meta_data[\"{2}\"] = \"{1}\"",
                                                                                                                                        "storeas" : "content"
                                                                                                                                        }
                                                                                                                              },
                                                                                                              },
                                                                                                     "Qmean" : {
                                                                                                                "storeas" : "content",
                                                                                                                "variable" : "{0}.meta_data[\"{2}\"] = {1}",
                                                                                                                "attributes" : {"unit" : {"variable" : "{0}.meta_data[\"{2}\"] = \"{1}\""}},
                                                                                                                },
                                                                                                     "Shadowfactor" : {
                                                                                                                       "variable" : "{0}.meta_data[\"{2}\"] = \"{1}\"",
                                                                                                                       "storeas" : "content",
                                                                                                                       },
                                                                                                     "<any>" : {
                                                                                                                "variable" : "{0}.meta_data[\"{2}\"] = \"{1}\"",
                                                                                                                "storeas" : "content",
                                                                                                                }
                                                                                                     }
                                                                                       },
                                                                            "<any>" : {"variable" : "{0}.meta_data[\"{2}\"] = \"{1}\"",}
                                                                            }
                                                              },
                                                 "SAStransmission_spectrum" : {
                                                                               "children" : {
                                                                                             "Tdata" : {
                                                                                                        "children" : {
                                                                                                                      "Lambda" : {
                                                                                                                                  "variable" : "{0}.meta_data[\"{2}\"] = \"{1}\"",
                                                                                                                                  "attributes" : {"unit" : {"variable" : "{0}.meta_data[\"{2}\"] = \"{1}\""}}
                                                                                                                                  },
                                                                                                                      "T" : {
                                                                                                                             "variable" : "{0}.meta_data[\"{2}\"] = \"{1}\"",
                                                                                                                             "attributes" : {"unit" : {"variable" : "{0}.meta_data[\"{2}\"] = \"{1}\""}}
                                                                                                                             },
                                                                                                                      "Tdev" : {
                                                                                                                                "variable" : "{0}.meta_data[\"{2}\"] = \"{1}\"",
                                                                                                                                "attributes" : {"unit" : {"variable" : "{0}.meta_data[\"{2}\"] = \"{1}\""}}
                                                                                                                                },
                                                                                                                      "<any>" : {"variable" : "{0}.meta_data[\"{2}\"] = \"{1}\""},
                                                                                                                      }
                                                                                                        },
                                                                                             "<any>" : {"variable" : "{0}.meta_data[\"{2}\"] = \"{1}\""},
                                                                                             },
                                                                               "attributes" : {"name" : {"variable" : "{0}.meta_data[\"{2}\"] = \"{1}\""},
                                                                                               "timestamp" : {"variable" : "{0}.meta_data[\"{2}\"] = \"{1}\""},}
                                                                               },
                                                 "SASsample" : {
                                                                "attributes" : {"name" : {"variable" : "{0}.sample.name = \"{1}\""},},
                                                                "children" : {
                                                                              "ID" : {"variable" : "{0}.sample.ID = \"{1}\""},
                                                                              "thickness" : {
                                                                                             "variable" : "{0}.sample.thickness = {1}",
                                                                                             "unit" : "sample.thickness_unit",
                                                                                             "storeas" : "float",
                                                                                             "attributes" : {
                                                                                                             "units" : {
                                                                                                                        "variable" : "{0}.sample.thickness_unit = \"{1}\"",
                                                                                                                        "storeas" : "content"
                                                                                                                        }
                                                                                                             },
                                                                                             },
                                                                              "transmission" : {
                                                                                                "variable" : "{0}.sample.transmission = {1}",
                                                                                                "storeas" : "float",
                                                                                                }, 
                                                                              "temperature" : {
                                                                                               "variable" : "{0}.sample.temperature = {1}",
                                                                                               "unit" : "sample.temperature_unit",
                                                                                               "storeas" : "float",
                                                                                               "attributes" : {
                                                                                                               "units" : {
                                                                                                                          "variable" : "{0}.sample.temperature_unit = \"{1}\"",
                                                                                                                          "storeas" : "content"
                                                                                                                          }
                                                                                                               },
                                                                                               }, 
                                                                              "position" : {
                                                                                            "children" : {
                                                                                                          "x" : {
                                                                                                                 "variable" : "{0}.sample.position.x = {1}",
                                                                                                                 "unit" : "sample.position_unit",
                                                                                                                 "storeas" : "float",
                                                                                                                 "attributes" : {
                                                                                                                                 "units" : {
                                                                                                                                            "variable" : "{0}.sample.position_unit = \"{1}\"",
                                                                                                                                            "storeas" : "content"
                                                                                                                                            }
                                                                                                                                 }
                                                                                                                 },
                                                                                                          "y" : {
                                                                                                                 "variable" : "{0}.sample.position.y = {1}",
                                                                                                                 "unit" : "sample.position_unit",
                                                                                                                 "attributes" : {
                                                                                                                                 "units" : {
                                                                                                                                            "variable" : "{0}.sample.position_unit = \"{1}\"",
                                                                                                                                            "storeas" : "content"
                                                                                                                                            }
                                                                                                                                 }
                                                                                                                 },
                                                                                                          "z" : {
                                                                                                                 "variable" : "{0}.sample.position.z = {1}",
                                                                                                                 "unit" : "sample.position_unit",
                                                                                                                 "attributes" : {
                                                                                                                                 "units" : {
                                                                                                                                            "variable" : "{0}.sample.position_unit = \"{1}\"",
                                                                                                                                            "storeas" : "content"
                                                                                                                                            }
                                                                                                                                 }
                                                                                                                 },
                                                                                                          },
                                                                                            },
                                                                              "orientation" : {
                                                                                               "children" : {
                                                                                                             "roll" : {
                                                                                                                       "variable" : "{0}.sample.orientation.x = {1}",
                                                                                                                       "unit" : "sample.orientation_unit",
                                                                                                                       "storeas" : "float",
                                                                                                                       "attributes" : {
                                                                                                                                       "units" : {
                                                                                                                                                  "variable" : "{0}.sample.orientation_unit = \"{1}\"",
                                                                                                                                                  "storeas" : "content"
                                                                                                                                                  }
                                                                                                                                       }
                                                                                                                       },
                                                                                                             "pitch" : {
                                                                                                                       "variable" : "{0}.sample.orientation.y = {1}",
                                                                                                                       "unit" : "sample.orientation_unit",
                                                                                                                       "storeas" : "float",
                                                                                                                       "attributes" : {
                                                                                                                                       "units" : {
                                                                                                                                                  "variable" : "{0}.sample.orientation_unit = \"{1}\"",
                                                                                                                                                  "storeas" : "content"
                                                                                                                                                  }
                                                                                                                                       }
                                                                                                                       },
                                                                                                             "yaw" : {
                                                                                                                       "variable" : "{0}.sample.orientation.z = {1}",
                                                                                                                       "unit" : "sample.orientation_unit",
                                                                                                                       "storeas" : "float",
                                                                                                                       "attributes" : {
                                                                                                                                       "units" : {
                                                                                                                                                  "variable" : "{0}.sample.orientation_unit = \"{1}\"",
                                                                                                                                                  "storeas" : "content"
                                                                                                                                                  }
                                                                                                                                       }
                                                                                                                       },
                                                                                                             },
                                                                                               },
                                                                              "details" : {"variable" : "{0}.sample.details.append(\"{1}\")"},
                                                                              "<any>" : {"variable" : "{0}.meta_data[\"{2}\"] = \"{1}\""}
                                                                              },
                                                                },
                                                 "SASinstrument" : {
                                                                    "children" : {
                                                                                  "name" : {"variable" : "{0}.instrument = \"{1}\""},
                                                                                  "SASsource" : {
                                                                                                 "attributes" : {"name" : {"variable" : "{0}.source.name = \"{1}\""}},
                                                                                                 "children" : {
                                                                                                               "radiation" : {"variable" : "{0}.source.radiation = \"{1}\""},
                                                                                                               "beam_size" : {
                                                                                                                              "attributes" : {"name" : {"variable" : "{0}.source.beam_size_name = \"{1}\""}},
                                                                                                                              "children" : {
                                                                                                                                            "x" : {
                                                                                                                                                   "variable" : "{0}.source.beam_size.x = {1}",
                                                                                                                                                   "unit" : "source.beam_size_unit",
                                                                                                                                                   "storeas" : "float",
                                                                                                                                                   "attributes" : {
                                                                                                                                                                   "unit" : "{0}.source.beam_size_unit = \"{1}\"",
                                                                                                                                                                   "storeas" : "content"
                                                                                                                                                                   }
                                                                                                                                                   },
                                                                                                                                            "y" : {
                                                                                                                                                   "variable" : "{0}.source.beam_size.y = {1}",
                                                                                                                                                   "unit" : "source.beam_size_unit",
                                                                                                                                                   "storeas" : "float",
                                                                                                                                                   "attributes" : {
                                                                                                                                                                   "unit" : "{0}.source.beam_size_unit = \"{1}\"",
                                                                                                                                                                   "storeas" : "content"
                                                                                                                                                                   }
                                                                                                                                                   },
                                                                                                                                            "z" : {
                                                                                                                                                   "variable" : "{0}.source.beam_size.z = {1}",
                                                                                                                                                   "unit" : "source.beam_size_unit",
                                                                                                                                                   "storeas" : "float",
                                                                                                                                                   "attributes" : {
                                                                                                                                                                   "unit" : "{0}.source.beam_size_unit = \"{1}\"",
                                                                                                                                                                   "storeas" : "content"
                                                                                                                                                                   }
                                                                                                                                                   },
                                                                                                                                            }
                                                                                                                              },
                                                                                                               "beam_shape" : {"variable" : "{0}.source.beam_shape = \"{1}\""},
                                                                                                               "wavelength" : {
                                                                                                                               "variable" : "{0}.source.wavelength = {1}",
                                                                                                                               "unit" : "source.wavelength_unit",
                                                                                                                               "storeas" : "float",
                                                                                                                               "attributes" : {
                                                                                                                                               "unit" : {
                                                                                                                                                         "variable" : "{0}.source.wavelength_unit = \"{1}\"",
                                                                                                                                                         "storeas" : "content"
                                                                                                                                                         },
                                                                                                                                               }
                                                                                                                               },
                                                                                                               "wavelength_min" : {
                                                                                                                                  "variable" : "{0}.source.wavelength_min = {1}",
                                                                                                                                  "unit" : "source.wavelength_min_unit",
                                                                                                                                  "storeas" : "float",
                                                                                                                                  "attributes" : {
                                                                                                                                                  "unit" : {
                                                                                                                                                            "variable" : "{0}.source.wavelength_min_unit = \"{1}\"",  
                                                                                                                                                            "storeas" : "content"
                                                                                                                                                            },
                                                                                                                                                  }
                                                                                                                                  },
                                                                                                               "wavelength_max" : {
                                                                                                                                   "variable" : "{0}.source.wavelength_max = {1}",
                                                                                                                                   "unit" : "source.wavelength_max_unit",
                                                                                                                                   "storeas" : "float",
                                                                                                                                   "attributes" : {
                                                                                                                                                   "unit" : {
                                                                                                                                                             "variable" : "{0}.source.wavelength_max_unit = \"{1}\"",
                                                                                                                                                             "storeas" : "content"
                                                                                                                                                             },
                                                                                                                                                   }
                                                                                                                                   },
                                                                                                               "wavelength_spread" : {
                                                                                                                                      "variable" : "{0}.source.wavelength_spread = {1}",
                                                                                                                                      "unit" : "source.wavelength_spread_unit",
                                                                                                                                      "storeas" : "float",
                                                                                                                                      "attributes" : {
                                                                                                                                                      "unit" : {"variable" : "{0}.source.wavelength_spread_unit = \"{1}\""},
                                                                                                                                                      "storeas" : "content"
                                                                                                                                                      }
                                                                                                                                      },
                                                                                                               },
                                                                                                 },
                                                                                  "SAScollimation" : {
                                                                                                      "attributes" : {"name" : {"variable" : "{0}.name = \"{1}\""}},
                                                                                                      "variable" : None,
                                                                                                      "children" : {
                                                                                                                    "length" : {
                                                                                                                                "variable" : "{0}.length = {1}",
                                                                                                                                "unit" : "length_unit",
                                                                                                                                "storeas" : "float",
                                                                                                                                "attributes" : {
                                                                                                                                                "storeas" : "content",
                                                                                                                                                "unit" : {"variable" : "{0}.length_unit = \"{1}\""}
                                                                                                                                                },
                                                                                                                                },
                                                                                                                    "aperture" : {
                                                                                                                                  "attributes" : {
                                                                                                                                                  "name" : {"variable" : "{0}.name = \"{1}\""},
                                                                                                                                                  "type" : {"variable" : "{0}.type = \"{1}\""},
                                                                                                                                                  },
                                                                                                                                  "children" : {
                                                                                                                                                "size" : {
                                                                                                                                                          "attributes" : {"unit" : {"variable" : "{0}.size_unit = \"{1}\""}},
                                                                                                                                                          "children" : {
                                                                                                                                                                        "storeas" : "float",
                                                                                                                                                                        "x" : {
                                                                                                                                                                               "variable" : "{0}.size.x = {1}",
                                                                                                                                                                               "unit" : "size_unit",
                                                                                                                                                                               "storeas" : "float",
                                                                                                                                                                               "attributes" : {
                                                                                                                                                                                               "unit" : {
                                                                                                                                                                                                         "variable" : "{0}.size_unit = \"{1}\"",
                                                                                                                                                                                                         "storeas" : "content"
                                                                                                                                                                                                         },                                    }
                                                                                                                                                                               },
                                                                                                                                                                        "y" : {
                                                                                                                                                                               "variable" : "{0}.size.y = {1}",
                                                                                                                                                                               "unit" : "size_unit",
                                                                                                                                                                               "storeas" : "float",
                                                                                                                                                                               "attributes" : {
                                                                                                                                                                                               "unit" : {
                                                                                                                                                                                                         "variable" : "{0}.size_unit = \"{1}\"",
                                                                                                                                                                                                         "storeas" : "content"
                                                                                                                                                                                                         },
                                                                                                                                                                                               }
                                                                                                                                                                               },
                                                                                                                                                                        "z" : {
                                                                                                                                                                               "variable" : "{0}.size.z = {1}",
                                                                                                                                                                               "unit" : "size_unit",
                                                                                                                                                                               "storeas" : "float",
                                                                                                                                                                               "attributes" : {
                                                                                                                                                                                               "unit" : {
                                                                                                                                                                                                         "variable" : "{0}.size_unit = \"{1}\"",
                                                                                                                                                                                                         "storeas" : "content"
                                                                                                                                                                                                         },
                                                                                                                                                                                              }
                                                                                                                                                                               },
                                                                                                                                                                        }
                                                                                                                                                          },
                                                                                                                                                "distance" : {"attributes" : {"unit" : {"variable" : "{0}.distance_unit = \"{1}\""}},
                                                                                                                                                              "variable" : "{0}.distance = {1}",
                                                                                                                                                              "unit" : "length_unit",
                                                                                                                                                              }
                                                                                                                                                }
                                                                                                                                  },
                                                                                                                    },
                                                                                                      },
                                                                                  "SASdetector" : {
                                                                                                   "storeas" : "float",
                                                                                                   "variable" : None,
                                                                                                   "attributes" : {
                                                                                                                   "name" : {
                                                                                                                             "storeas" : "content",
                                                                                                                             "variable" : "{0}.name = \"{1}\"",
                                                                                                                             }
                                                                                                                   },
                                                                                                   "children" : {
                                                                                                                 "name" : {
                                                                                                                           "storeas" : "content",
                                                                                                                           "variable" : "{0}.name = \"{1}\"",
                                                                                                                           },
                                                                                                                 "SDD" : {
                                                                                                                          "variable" : "{0}.distance = {1}",
                                                                                                                          "unit" : "distance_unit",
                                                                                                                          "attributes" : {
                                                                                                                                          "unit" : {
                                                                                                                                                    "variable" : "{0}.distance_unit = \"{1}\"",
                                                                                                                                                    "storeas" : "content"
                                                                                                                                                    }
                                                                                                                                          },
                                                                                                                          },
                                                                                                                 "offset" : {
                                                                                                                             "children" : {
                                                                                                                                           "x" : {
                                                                                                                                                  "variable" : "{0}.offset.x = {1}",
                                                                                                                                                  "unit" : "offset_unit",
                                                                                                                                                  "attributes" : {
                                                                                                                                                                  "unit" : {
                                                                                                                                                                            "variable" : "{0}.offset_unit = \"{1}\"",
                                                                                                                                                                            "storeas" : "content"
                                                                                                                                                                            },
                                                                                                                                                                  }
                                                                                                                                                  },
                                                                                                                                           "y" : {
                                                                                                                                                  "variable" : "{0}.offset.y = {1}",
                                                                                                                                                  "unit" : "offset_unit",
                                                                                                                                                  "attributes" : {
                                                                                                                                                                  "unit" : {
                                                                                                                                                                            "variable" : "{0}.offset_unit = \"{1}\"",
                                                                                                                                                                            "storeas" : "content"
                                                                                                                                                                            },
                                                                                                                                                                  }
                                                                                                                                                  },
                                                                                                                                           "z" : {
                                                                                                                                                  "variable" : "{0}.offset.z = {1}",
                                                                                                                                                  "unit" : "offset_unit",
                                                                                                                                                  "attributes" : {
                                                                                                                                                                  "unit" : {
                                                                                                                                                                            "variable" : "{0}.offset_unit = \"{1}\"",
                                                                                                                                                                            "storeas" : "content"
                                                                                                                                                                            },
                                                                                                                                                                  }
                                                                                                                                                  },
                                                                                                                                           }
                                                                                                                             },
                                                                                                                 "orientation" : {
                                                                                                                                  "children" : {
                                                                                                                                                "roll" : {
                                                                                                                                                          "variable" : "{0}.orientation.x = {1}",
                                                                                                                                                          "unit" : "orientation_unit",
                                                                                                                                                          "attributes" : {
                                                                                                                                                                          "unit" : "{0}.orientation_unit = \"{1}\"",
                                                                                                                                                                          "storeas" : "content"
                                                                                                                                                                          }
                                                                                                                                                          },
                                                                                                                                                "pitch" : {
                                                                                                                                                           "variable" : "{0}.orientation.y = {1}",
                                                                                                                                                           "unit" : "orientation_unit",
                                                                                                                                                           "attributes" : {
                                                                                                                                                                           "unit" : "{0}.orientation_unit = \"{1}\"",
                                                                                                                                                                           "storeas" : "content"
                                                                                                                                                                           }
                                                                                                                                                           },
                                                                                                                                                "yaw" : {
                                                                                                                                                         "variable" : "{0}.orientation.z = {1}",
                                                                                                                                                         "unit" : "orientation_unit",
                                                                                                                                                         "attributes" : {
                                                                                                                                                                         "unit" : "{0}.orientation_unit = \"{1}\"",
                                                                                                                                                                         "storeas" : "content"
                                                                                                                                                                         }
                                                                                                                                                         },
                                                                                                                                                }
                                                                                                                                  },
                                                                                                                 "beam_center" : {
                                                                                                                                  "children" : {
                                                                                                                                                "x" : {
                                                                                                                                                       "variable" : "{0}.beam_center.x = {1}",
                                                                                                                                                       "unit" : "beam_center_unit",
                                                                                                                                                       "attributes" : {
                                                                                                                                                                       "unit" : "{0}.beam_center_unit = \"{1}\"",
                                                                                                                                                                       "storeas" : "content"
                                                                                                                                                                       }
                                                                                                                                                  },
                                                                                                                                                "y" : {
                                                                                                                                                       "variable" : "{0}.beam_center.y = {1}",
                                                                                                                                                       "unit" : "beam_center_unit",
                                                                                                                                                       "attributes" : {
                                                                                                                                                                       "unit" : "{0}.beam_center_unit = \"{1}\"",
                                                                                                                                                                       "storeas" : "content"
                                                                                                                                                                       }
                                                                                                                                                       },
                                                                                                                                                "z" : {
                                                                                                                                                       "variable" : "{0}.beam_center.z = {1}",
                                                                                                                                                       "unit" : "beam_center_unit",
                                                                                                                                                       "attributes" : {
                                                                                                                                                                       "unit" : "{0}.beam_center_unit = \"{1}\"",
                                                                                                                                                                       "storeas" : "content"
                                                                                                                                                                       }
                                                                                                                                                       },
                                                                                                                                                }
                                                                                                                                  },
                                                                                                                 "pixel_size" : {
                                                                                                                                 "children" : {
                                                                                                                                               "x" : {
                                                                                                                                                      "variable" : "{0}.pixel_size.x = {1}",
                                                                                                                                                      "unit" : "pixel_size_unit",
                                                                                                                                                      "attributes" : {
                                                                                                                                                                      "unit" : "{0}.pixel_size_unit = \"{1}\"",
                                                                                                                                                                      "storeas" : "content"
                                                                                                                                                                      }
                                                                                                                                                      },
                                                                                                                                                "y" : {
                                                                                                                                                       "variable" : "{0}.pixel_size.y = {1}",
                                                                                                                                                       "unit" : "pixel_size_unit",
                                                                                                                                                      "attributes" : {
                                                                                                                                                                       "unit" : "{0}.pixel_size_unit = \"{1}\"",
                                                                                                                                                                       "storeas" : "content"
                                                                                                                                                                       }
                                                                                                                                                       },
                                                                                                                                                "z" : {
                                                                                                                                                       "variable" : "{0}.pixel_size.z = {1}",
                                                                                                                                                       "unit" : "pixel_size_unit",
                                                                                                                                                      "attributes" : {
                                                                                                                                                                       "unit" : "{0}.pixel_size_unit = \"{1}\"",
                                                                                                                                                                       "storeas" : "content"
                                                                                                                                                                       }
                                                                                                                                                       },
                                                                                                                                                }
                                                                                                                                  },
                                                                                                                 "slit_length" : {
                                                                                                                                  "variable" : "{0}.slit_length = {1}",
                                                                                                                                  "unit" : "slit_length_unit",
                                                                                                                                  "attributes" : {
                                                                                                                                                  "unit" : {
                                                                                                                                                            "variable" : "{0}.slit_length_unit = \"{1}\"",
                                                                                                                                                            "storeas" : "content"
                                                                                                                                                            }
                                                                                                                                                  }
                                                                                                                                  }
                                                                                                                  },
                                                                                                   },
                                                                                   },
                                                                    },
                                                 "SASprocess" : {
                                                                 "variable" : " ",
                                                                 "children" : {
                                                                               "name" : {"variable" : "{0}.name = \"{1}\""},
                                                                               "date" : {"variable" : "{0}.date = \"{1}\""},
                                                                               "description" : {"variable" : "{0}.description = \"{1}\""},
                                                                               "term" : {
                                                                                         "variable" : None,
                                                                                         "attributes" : {
                                                                                                         "unit" : {"variable" : None},
                                                                                                         "name" : {"variable" : None}
                                                                                                         }
                                                                                         },
                                                                               "SASprocessnote" : {"children" : {"<any>" : {"variable" : "{0}.notes.append(\"{2}: {1}\")"}}},
                                                                               "<any>" : {"variable" : "{0}.notes.append(\"{2}: {1}\")",}
                                                                               },
                                                                 },
                                                 "SASnote" : {"variable" : "{0}.notes.append(\"{1}\")"},
                                                 "<any>" : {"variable" : "{0}.meta_data[\"{2}\" = \"{1}\""},
                                                 }
                                   }
                     }