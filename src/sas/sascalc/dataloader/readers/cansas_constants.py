"""
Information relating to the CanSAS data format. These constants are used in
the cansas_reader.py file to read in any version of the cansas format.
"""
class CansasConstants(object):
    """
    The base class to define where all of the data is to be saved by
    cansas_reader.py.
    """
    names = ''
    format = ''

    def __init__(self):
        self.names = self.CANSAS_NS
        self.format = self.CANSAS_FORMAT

    def iterate_namespace(self, namespace):
        """
        Method to iterate through a cansas constants tree based on a list of
        names

        :param namespace: A list of names that match the tree structure of
            cansas_constants
        """
        # The current level to look through in cansas_constants.
        return_me = CurrentLevel()
        return_me.current_level = self.CANSAS_FORMAT.get("SASentry")
        # Defaults for variable and datatype
        return_me.ns_datatype = "content"
        return_me.ns_optional = True
        for name in namespace:
            try:
                if name != "SASentry":
                    return_me.current_level = \
                        return_me.current_level.get("children").get(name, "")
                    if return_me.current_level == "":
                        return_me.current_level = \
                                return_me.current_level.get("<any>", "")
                    cl_datatype = return_me.current_level.get("storeas", "")
                    cl_units_optional = \
                             return_me.current_level.get("units_optional", "")
                    # Where are how to store the variable for the given
                    # namespace CANSAS_CONSTANTS tree is hierarchical, so
                    # is no value, inherit
                    return_me.ns_datatype = cl_datatype if cl_datatype != "" \
                        else return_me.ns_datatype
                    return_me.ns_optional = cl_units_optional if \
                        cl_units_optional != return_me.ns_optional \
                                        else return_me.ns_optional
            except AttributeError:
                return_me.ns_datatype = "content"
                return_me.ns_optional = True
        return return_me

    def get_namespace_map(self):
        """
        Helper method to get the names namespace list
        """
        return self.names

    # CANSAS_NS holds the base namespace and default schema file information
    CANSAS_NS = {"1.0" : {"ns" : "cansas1d/1.0",
                          "schema" : "cansas1d_v1_0.xsd"
                         },
                 "1.1" : {"ns" : "urn:cansas1d:1.1",
                          "schema" : "cansas1d_v1_1.xsd"
                         }
                }

    # The constants below hold information on where to store the CanSAS data
    # when loaded in using sasview
    ANY = {"storeas" : "content"}
    TITLE = {}
    SASNOTE = {}
    SASPROCESS_TERM = {"attributes" : {"unit" : {}, "name" : {}}}
    SASPROCESS_SASPROCESSNOTE = {"children" : {"<any>" : ANY}}
    SASPROCESS = {"children" : {"name" : {},
                                "date" : {},
                                "description" : {},
                                "term" : SASPROCESS_TERM,
                                "SASprocessnote" : SASPROCESS_SASPROCESSNOTE,
                                "<any>" : ANY
                               },
                 }
    RUN = {"attributes" : {"name" :{}}}
    SASDATA_IDATA_Q = {"units_optional" : False,
                       "storeas" : "float",
                        "unit" : "x_unit",
                       "attributes" : {"unit" : {"storeas" : "content"}},
                      }
    SASDATA_IDATA_I = {"units_optional" : False,
                       "storeas" : "float",
                        "unit" : "y_unit",
                       "attributes" : {"unit" : {"storeas" : "content"}},
                      }
    SASDATA_IDATA_IDEV = {"units_optional" : False,
                          "storeas" : "float",
                          "unit" : "y_unit",
                          "attributes" : {"unit" : {"storeas" : "content"}},
                         }
    SASDATA_IDATA_QDEV = {"units_optional" : False,
                          "storeas" : "float",
                          "unit" : "x_unit",
                          "attributes" : {"unit" : {"storeas" : "content"}},
                         }
    SASDATA_IDATA_DQL = {"units_optional" : False,
                         "storeas" : "float",
                         "unit" : "x_unit",
                         "attributes" : {"unit" : {"storeas" : "content"}},
                        }
    SASDATA_IDATA_DQW = {"units_optional" : False,
                         "storeas" : "float",
                         "unit" : "x_unit",
                         "attributes" : {"unit" : {"storeas" : "content"}},
                        }
    SASDATA_IDATA_QMEAN = {"unit" : "x_unit",
                           "attributes" : {"unit" : {}},
                          }
    SASDATA_IDATA_SHADOWFACTOR = {}
    SASDATA_IDATA = {"attributes" : {"name" : {},"timestamp" : {"storeas" : "timestamp"}},
                     "children" : {"Q" : SASDATA_IDATA_Q,
                                   "I" : SASDATA_IDATA_I,
                                   "Idev" : SASDATA_IDATA_IDEV,
                                   "Qdev" : SASDATA_IDATA_QDEV,
                                   "dQw" : SASDATA_IDATA_DQW,
                                   "dQl" : SASDATA_IDATA_DQL,
                                   "Qmean" : SASDATA_IDATA_QMEAN,
                                   "Shadowfactor" : SASDATA_IDATA_SHADOWFACTOR,
                                   "<any>" : ANY
                                  }
                    }
    SASDATA = {"attributes" : {"name" : {}},
               "variable" : None,
               "children" : {"Idata" : SASDATA_IDATA,
                             "Sesans": {"storeas": "content"},
                             "zacceptance": {"storeas": "float"},
                             "yacceptance": {"storeas": "float"},
                             "<any>" : ANY
                            }
              }
    SASTRANSSPEC_TDATA_LAMDBA = {"storeas" : "float",
                                 "unit" : "wavelength_unit",
                                 "attributes" : {"unit" : {"storeas" : "content"}}
                                }
    SASTRANSSPEC_TDATA_T = {"storeas" : "float",
                            "unit" : "transmission_unit",
                            "attributes" : {"unit" : {"storeas" : "content"}}
                           }
    SASTRANSSPEC_TDATA_TDEV = {"storeas" : "float",
                               "unit" : "transmission_deviation_unit",
                               "attributes" : {"unit" :{"storeas" : "content"}}
                              }
    SASTRANSSPEC_TDATA = {"children" : {"Lambda" : SASTRANSSPEC_TDATA_LAMDBA,
                                        "T" : SASTRANSSPEC_TDATA_T,
                                        "Tdev" : SASTRANSSPEC_TDATA_TDEV,
                                        "<any>" : ANY,
                                       }
                         }
    SASTRANSSPEC = {"children" : {"Tdata" : SASTRANSSPEC_TDATA,
                                  "<any>" : ANY,
                                 },
                    "attributes" : {"name" :{}, "timestamp" : {},}
                   }
    SASSAMPLE_THICK = {"unit" : "thickness_unit",
                       "storeas" : "float",
                       "attributes" : {"unit" :{}},
                      }
    SASSAMPLE_TRANS = {"storeas" : "float",}
    SASSAMPLE_TEMP = {"unit" : "temperature_unit",
                      "storeas" : "float",
                      "attributes" :{"unit" :{}},
                     }
    SASSAMPLE_POS_ATTR = {"unit" : {}}
    SASSAMPLE_POS_X = {"unit" : "position_unit",
                       "storeas" : "float",
                       "attributes" : SASSAMPLE_POS_ATTR
                      }
    SASSAMPLE_POS_Y = {"unit" : "position_unit",
                       "storeas" : "float",
                       "attributes" : SASSAMPLE_POS_ATTR
                      }
    SASSAMPLE_POS_Z = {"unit" : "position_unit",
                       "storeas" : "float",
                       "attributes" : SASSAMPLE_POS_ATTR
                      }
    SASSAMPLE_POS = {"children" : {"x" : SASSAMPLE_POS_X,
                                   "y" : SASSAMPLE_POS_Y,
                                   "z" : SASSAMPLE_POS_Z,
                                  },
                    }
    SASSAMPLE_ORIENT_ATTR = {"unit" :{}}
    SASSAMPLE_ORIENT_ROLL = {"unit" : "orientation_unit",
                             "storeas" : "float",
                             "attributes" : SASSAMPLE_ORIENT_ATTR
                            }
    SASSAMPLE_ORIENT_PITCH = {"unit" : "orientation_unit",
                              "storeas" : "float",
                              "attributes" : SASSAMPLE_ORIENT_ATTR
                             }
    SASSAMPLE_ORIENT_YAW = {"unit" : "orientation_unit",
                            "storeas" : "float",
                            "attributes" : SASSAMPLE_ORIENT_ATTR
                           }
    SASSAMPLE_ORIENT = {"children" : {"roll" : SASSAMPLE_ORIENT_ROLL,
                                      "pitch" : SASSAMPLE_ORIENT_PITCH,
                                      "yaw" : SASSAMPLE_ORIENT_YAW,
                                     },
                       }
    SASSAMPLE = {"attributes" :
                 {"name" : {},},
                 "children" : {"ID" : {},
                               "thickness" : SASSAMPLE_THICK,
                               "transmission" : SASSAMPLE_TRANS,
                               "temperature" : SASSAMPLE_TEMP,
                               "position" : SASSAMPLE_POS,
                               "orientation" : SASSAMPLE_ORIENT,
                               "details" : {},
                               "<any>" : ANY
                              },
                }
    SASINSTR_SRC_BEAMSIZE_ATTR = {"unit" : ""}
    SASINSTR_SRC_BEAMSIZE_X = {"unit" : "beam_size_unit",
                               "storeas" : "float",
                               "attributes" : SASINSTR_SRC_BEAMSIZE_ATTR
                              }
    SASINSTR_SRC_BEAMSIZE_Y = {"unit" : "beam_size_unit",
                               "storeas" : "float",
                               "attributes" : SASINSTR_SRC_BEAMSIZE_ATTR
                              }
    SASINSTR_SRC_BEAMSIZE_Z = {"unit" : "beam_size_unit",
                               "storeas" : "float",
                               "attributes" : SASINSTR_SRC_BEAMSIZE_ATTR
                              }
    SASINSTR_SRC_BEAMSIZE = {"attributes" : {"name" : {}},
                             "children" : {"x" : SASINSTR_SRC_BEAMSIZE_X,
                                           "y" : SASINSTR_SRC_BEAMSIZE_Y,
                                           "z" : SASINSTR_SRC_BEAMSIZE_Z,
                                          }
                            }
    SASINSTR_SRC_WL = {"unit" : "wavelength_unit",
                       "storeas" : "float",
                       "attributes" : {"unit" :{},
                       }
                      }
    SASINSTR_SRC_WL_MIN = {"unit" : "wavelength_min_unit",
                           "storeas" : "float",
                           "attributes" : {"unit" :{"storeas" : "content"},}
                          }
    SASINSTR_SRC_WL_MAX = {"unit" : "wavelength_max_unit",
                           "storeas" : "float",
                           "attributes" : {"unit" :{"storeas" : "content"},}
                          }
    SASINSTR_SRC_WL_SPR = {"unit" : "wavelength_spread_unit",
                           "storeas" : "float",
                           "attributes" : {"unit" : {"storeas" : "content"},}
                          }
    SASINSTR_SRC = {"attributes" : {"name" : {}},
                    "children" : {"radiation" : {},
                                  "beam_size" : SASINSTR_SRC_BEAMSIZE,
                                  "beam_shape" : {},
                                  "wavelength" : SASINSTR_SRC_WL,
                                  "wavelength_min" : SASINSTR_SRC_WL_MIN,
                                  "wavelength_max" : SASINSTR_SRC_WL_MAX,
                                  "wavelength_spread" : SASINSTR_SRC_WL_SPR,
                                 },
                   }
    SASINSTR_COLL_APER_ATTR = {"unit" : {}}
    SASINSTR_COLL_APER_X = {"unit" : "size_unit",
                            "storeas" : "float",
                            "attributes" : SASINSTR_COLL_APER_ATTR
                           }
    SASINSTR_COLL_APER_Y = {"unit" : "size_unit",
                            "storeas" : "float",
                            "attributes" : SASINSTR_COLL_APER_ATTR
                           }
    SASINSTR_COLL_APER_Z = {"unit" : "size_unit",
                            "storeas" : "float",
                            "attributes" : SASINSTR_COLL_APER_ATTR
                           }
    SASINSTR_COLL_APER_SIZE = {"attributes" : {"unit" : {}},
                               "children" : {"storeas" : "float",
                                             "x" : SASINSTR_COLL_APER_X,
                                             "y" : SASINSTR_COLL_APER_Y,
                                             "z" : SASINSTR_COLL_APER_Z,
                                            }
                              }
    SASINSTR_COLL_APER_DIST = {"storeas" : "float",
                               "attributes" : {"unit" : {}},
                               "unit" : "distance_unit",
                              }
    SASINSTR_COLL_APER = {"attributes" : {"name" : {}, "type" : {}, },
                          "children" : {"size" : SASINSTR_COLL_APER_SIZE,
                                        "distance" : SASINSTR_COLL_APER_DIST
                                       }
                         }
    SASINSTR_COLL = {"attributes" : {"name" : {}},
                     "children" :
                         {"length" :
                          {"unit" : "length_unit",
                           "storeas" : "float",
                           "attributes" : {"storeas" : "content", "unit" : {}},
                          },
                          "aperture" : SASINSTR_COLL_APER,
                         },
                    }
    SASINSTR_DET_SDD = {"storeas" : "float",
                        "unit" : "distance_unit",
                        "attributes" : {"unit" :{}},
                       }
    SASINSTR_DET_OFF_ATTR = {"unit" : {"storeas" : "content" }}
    SASINSTR_DET_OFF_X = {"storeas" : "float",
                          "unit" : "offset_unit",
                          "attributes" : SASINSTR_DET_OFF_ATTR
                         }
    SASINSTR_DET_OFF_Y = {"storeas" : "float",
                          "unit" : "offset_unit",
                          "attributes" : SASINSTR_DET_OFF_ATTR
                         }
    SASINSTR_DET_OFF_Z = {"storeas" : "float",
                          "unit" : "offset_unit",
                          "attributes" : SASINSTR_DET_OFF_ATTR
                         }
    SASINSTR_DET_OFF = {"children" : {"x" : SASINSTR_DET_OFF_X,
                                      "y" : SASINSTR_DET_OFF_Y,
                                      "z" : SASINSTR_DET_OFF_Z,
                                     }
                       }
    SASINSTR_DET_OR_ATTR = {}
    SASINSTR_DET_OR_ROLL = {"storeas" : "float",
                            "unit" : "orientation_unit",
                            "attributes" : SASINSTR_DET_OR_ATTR
                           }
    SASINSTR_DET_OR_PITCH = {"storeas" : "float",
                             "unit" : "orientation_unit",
                             "attributes" : SASINSTR_DET_OR_ATTR
                            }
    SASINSTR_DET_OR_YAW = {"storeas" : "float",
                           "unit" : "orientation_unit",
                           "attributes" : SASINSTR_DET_OR_ATTR
                          }
    SASINSTR_DET_OR = {"children" : {"roll" : SASINSTR_DET_OR_ROLL,
                                     "pitch" : SASINSTR_DET_OR_PITCH,
                                     "yaw" : SASINSTR_DET_OR_YAW,
                                    }
                      }
    SASINSTR_DET_BC_X = {"storeas" : "float",
                         "unit" : "beam_center_unit",
                         "attributes" : {"storeas" : "content"}
                        }
    SASINSTR_DET_BC_Y = {"storeas" : "float",
                         "unit" : "beam_center_unit",
                         "attributes" : {"storeas" : "content"}
                        }
    SASINSTR_DET_BC_Z = {"storeas" : "float",
                         "unit" : "beam_center_unit",
                         "attributes" : {"storeas" : "content"}
                        }
    SASINSTR_DET_BC = {"children" : {"x" : SASINSTR_DET_BC_X,
                                     "y" : SASINSTR_DET_BC_Y,
                                     "z" : SASINSTR_DET_BC_Z,}
                      }
    SASINSTR_DET_PIXEL_X = {"storeas" : "float",
                            "unit" : "pixel_size_unit",
                            "attributes" : {"storeas" : "content" }
                           }
    SASINSTR_DET_PIXEL_Y = {"storeas" : "float",
                            "unit" : "pixel_size_unit",
                            "attributes" : {"storeas" : "content"}
                           }
    SASINSTR_DET_PIXEL_Z = {"storeas" : "float",
                            "unit" : "pixel_size_unit",
                            "attributes" : {"storeas" : "content"}
                           }
    SASINSTR_DET_PIXEL = {"children" : {"x" : SASINSTR_DET_PIXEL_X,
                                        "y" : SASINSTR_DET_PIXEL_Y,
                                        "z" : SASINSTR_DET_PIXEL_Z,
                                       }
                         }
    SASINSTR_DET_SLIT = {"storeas" : "float",
                         "unit" : "slit_length_unit",
                         "attributes" : {"unit" : {}}
                        }
    SASINSTR_DET = {"attributes" : {"name" : {"storeas" : "content"}},
                    "children" : {"name" : {"storeas" : "content"},
                                  "SDD" : SASINSTR_DET_SDD,
                                  "offset" : SASINSTR_DET_OFF,
                                  "orientation" : SASINSTR_DET_OR,
                                  "beam_center" : SASINSTR_DET_BC,
                                  "pixel_size" : SASINSTR_DET_PIXEL,
                                  "slit_length" : SASINSTR_DET_SLIT,
                                 }
                   }
    SASINSTR = {"children" :
                {"name" : {},
                 "SASsource" : SASINSTR_SRC,
                 "SAScollimation" : SASINSTR_COLL,
                 "SASdetector" : SASINSTR_DET,
                },
               }
    CANSAS_FORMAT = {"SASentry" :
                     {"units_optional" : True,
                      "storeas" : "content",
                      "attributes" : {"name" : {}},
                      "children" : {"Title" : TITLE,
                                    "Run" : RUN,
                                    "SASdata" : SASDATA,
                                    "SAStransmission_spectrum" : SASTRANSSPEC,
                                    "SASsample" : SASSAMPLE,
                                    "SASinstrument" : SASINSTR,
                                    "SASprocess" : SASPROCESS,
                                    "SASnote" : SASNOTE,
                                    "<any>" : ANY,
                                   }
                     }
                    }


class CurrentLevel(object):
    """
    A helper class to hold information on where you are in the constants tree
    """

    current_level = ''
    ns_datatype = ''
    ns_optional = True

    def __init__(self):
        self.current_level = {}
        self.ns_datatype = "content"
        self.ns_optional = True

    def get_current_level(self):
        """
        Helper method to get the current_level map
        """
        return self.current_level

    def get_data_type(self):
        """
        Helper method to get the ns_datatype label
        """
        return self.ns_datatype

    def get_variable(self):
        """
        Helper method to get the ns_variable label
        """
        return self.ns_variable
