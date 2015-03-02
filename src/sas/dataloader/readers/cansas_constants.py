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
        return_me.ns_variable = "{0}.meta_data[\"{2}\"] = \"{1}\""
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
                    cl_variable = return_me.current_level.get("variable", "")
                    cl_datatype = return_me.current_level.get("storeas", "")
                    cl_units_optional = \
                             return_me.current_level.get("units_required", "")
                    # Where are how to store the variable for the given
                    # namespace CANSAS_CONSTANTS tree is hierarchical, so
                    # is no value, inherit
                    return_me.ns_variable = cl_variable if cl_variable != "" \
                        else return_me.ns_variable
                    return_me.ns_datatype = cl_datatype if cl_datatype != "" \
                        else return_me.ns_datatype
                    return_me.ns_optional = cl_units_optional if \
                        cl_units_optional != return_me.ns_optional \
                                        else return_me.ns_optional
            except AttributeError:
                return_me.ns_variable = "{0}.meta_data[\"{2}\"] = \"{1}\""
                return_me.ns_datatype = "content"
                return_me.ns_optional = True
        return return_me

    def get_namespace_map(self):
        """
        Helper method to get the names namespace list
        """
        return self.names

    # CANSAS_NS holds the base namespace and default schema file information
    CANSAS_NS = {"1.0" : {
                         "ns" : "cansas1d/1.0",
                         "schema" : "cansas1d_v1_0.xsd"
                         },
                 "1.1" : {
                         "ns" : "urn:cansas1d:1.1",
                         "schema" : "cansas1d_v1_1.xsd"
                         }
                 }

    # The constants below hold information on where to store the CanSAS data
    # when loaded in using sasview
    META_DATA = "{0}.meta_data[\"{2}\"] = \"{1}\""
    ANY = {
           "variable" : "{0}.meta_data[\"{2}\"] = \'{1}\'",
           "storeas" : "content",
           }
    TITLE = {"variable" : "{0}.title = \"{1}\""}
    SASNOTE = {"variable" : "{0}.notes.append(\'{1}\')"}
    SASPROCESS_TERM = {"variable" : None,
                       "attributes" : {
                                       "unit" : {"variable" : None},
                                       "name" : {"variable" : None}
                                       }
                       }
    SASPROCESS_SASPROCESSNOTE = {"variable" : None,
                                 "children" : {"<any>" : ANY}
                                 }
    SASPROCESS = {"variable" : None,
                  "children" : {"name" : {"variable" : "{0}.name = \'{1}\'"},
                                "date" : {"variable" : "{0}.date = \'{1}\'"},
                                "description" : {"variable" : "{0}.description = \'{1}\'"},
                                "term" : SASPROCESS_TERM,
                                "SASprocessnote" : SASPROCESS_SASPROCESSNOTE,
                                "<any>" : ANY
                                },
                  }
    RUN = {"variable" : "{0}.run.append(\"{1}\")",
           "attributes" : {"name" : {"variable" : "{0}.run_name[node_value] = \"{1}\""}}
           }
    SASDATA_IDATA_Q = {"variable" : "{0}.x = numpy.append({0}.x, {1})",
                       "unit" : "x_unit",
                       "attributes" : {"unit" : {
                                                 "variable" : "{0}._xunit = \"{1}\"",
                                                 "storeas" : "content"
                                                 }
                                       },
                       }
    SASDATA_IDATA_I = {"variable" : "{0}.y = numpy.append({0}.y, {1})",
                       "unit" : "y_unit",
                       "attributes" : {"unit" : {
                                                 "variable" : "{0}._yunit = \"{1}\"",
                                                 "storeas" : "content"
                                                 }
                                       },
                       }
    SASDATA_IDATA_IDEV = {"variable" : "{0}.dy = numpy.append({0}.dy, {1})",
                          "unit" : "y_unit",
                          "attributes" : {"unit" : {
                                                    "variable" : META_DATA,
                                                    "storeas" : "content"
                                                    }
                                          },
                          }
    SASDATA_IDATA_QDEV = {"variable" : "{0}.dx = numpy.append({0}.dx, {1})",
                          "unit" : "x_unit",
                          "attributes" : {"unit" : {
                                                    "variable" : META_DATA,
                                                    "storeas" : "content"
                                                    }
                                          },
                          }
    SASDATA_IDATA_DQL = {
                         "variable" : "{0}.dxl = numpy.append({0}.dxl, {1})",
                         "unit" : "x_unit",
                         "attributes" : 
                         {
                          "unit" : 
                          {
                           "variable" : META_DATA,
                           "storeas" : "content"
                           }
                          },
                         }
    SASDATA_IDATA_DQW = {
                         "variable" : "{0}.dxw = numpy.append({0}.dxw, {1})",
                         "unit" : "x_unit",
                         "attributes" : 
                         {
                          "unit" : 
                          {
                           "variable" : META_DATA,
                           "storeas" : "content"
                           }
                          },
                         }
    SASDATA_IDATA_QMEAN = {
                           "storeas" : "content",
                           "unit" : "x_unit",
                           "variable" : META_DATA,
                           "attributes" : {"unit" : {"variable" : META_DATA}},
                           }
    SASDATA_IDATA_SHADOWFACTOR = {
                                  "variable" : META_DATA,
                                  "storeas" : "content",
                                  }
    SASDATA_IDATA = {
                     "storeas" : "float",
                     "units_optional" : False,
                     "variable" : None,
                     "attributes" : {
                                     "name" : {
                                               "variable" : META_DATA,
                                               "storeas" : "content",
                                               },
                                     "timestamp" : {
                                                    "variable" : META_DATA,
                                                    "storeas" : "timestamp",
                                                    }
                                     },
                     "children" : {
                                   "Q" : SASDATA_IDATA_Q,
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
    SASDATA = {
               "attributes" : {"name" : {"variable" : META_DATA,}},
               "variable" : None,
               "children" : {
                             "Idata" : SASDATA_IDATA,
                             "<any>" : ANY
                             }
               }
    SASTRANSSPEC_TDATA_LAMDBA = {
                                 "variable" : "{0}.wavelength.append({1})",
                                 "unit" : "wavelength_unit",
                                 "attributes" : 
                                 {
                                  "unit" : 
                                  {
                                   "variable" : \
                                    "{0}.wavelength_unit = \"{1}\"",
                                   "storeas" : "content"
                                   }
                                  }
                                 }
    SASTRANSSPEC_TDATA_T = {
                            "variable" : "{0}.transmission.append({1})",
                            "unit" : "transmission_unit",
                            "attributes" : 
                            {
                             "unit" : 
                             {
                              "variable" : "{0}.transmission_unit = \"{1}\"",
                              "storeas" : "content"
                              }
                             }
                            }
    SASTRANSSPEC_TDATA_TDEV = {
                               "variable" : \
                                    "{0}.transmission_deviation.append({1})",
                               "unit" : "transmission_deviation_unit",
                               "attributes" :
                               {
                                "unit" :
                                {
                                 "variable" : \
                                    "{0}.transmission_deviation_unit = \"{1}\"",
                                 "storeas" : "content"
                                 }
                                }
                               }
    SASTRANSSPEC_TDATA = {
                          "storeas" : "float",
                          "variable" : None,
                          "children" : {
                                        "Lambda" : SASTRANSSPEC_TDATA_LAMDBA,
                                        "T" : SASTRANSSPEC_TDATA_T,
                                        "Tdev" : SASTRANSSPEC_TDATA_TDEV,
                                        "<any>" : ANY,
                                        }
                          }
    SASTRANSSPEC = {
                    "variable" : None,
                    "children" : {
                                  "Tdata" : SASTRANSSPEC_TDATA,
                                  "<any>" : ANY,
                                  },
                    "attributes" : 
                    {
                     "name" :
                     {
                      "variable" : "{0}.name = \"{1}\""},
                      "timestamp" : 
                      {
                       "variable" : "{0}.timestamp = \"{1}\""
                       },
                     }
                    }
    SASSAMPLE_THICK = {
                       "variable" : "{0}.sample.thickness = {1}",
                       "unit" : "sample.thickness_unit",
                       "storeas" : "float",
                       "attributes" : 
                       {
                        "unit" : 
                        {
                         "variable" : "{0}.sample.thickness_unit = \"{1}\"",
                         "storeas" : "content"
                         }
                        },
                       }
    SASSAMPLE_TRANS = {
                       "variable" : "{0}.sample.transmission = {1}",
                       "storeas" : "float",
                       }
    SASSAMPLE_TEMP = {
                      "variable" : "{0}.sample.temperature = {1}",
                      "unit" : "sample.temperature_unit",
                      "storeas" : "float",
                      "attributes" : 
                      {
                       "unit" : 
                       {
                        "variable" : "{0}.sample.temperature_unit = \"{1}\"",
                        "storeas" : "content"
                        }
                       },
                      }
    SASSAMPLE_POS_ATTR = {
                          "unit" : {
                                     "variable" : \
                                        "{0}.sample.position_unit = \"{1}\"",
                                     "storeas" : "content"
                                     }
                          }
    SASSAMPLE_POS_X = {
                       "variable" : "{0}.sample.position.x = {1}",
                       "unit" : "sample.position_unit",
                       "storeas" : "float",
                       "attributes" : SASSAMPLE_POS_ATTR
                       }
    SASSAMPLE_POS_Y = {
                       "variable" : "{0}.sample.position.y = {1}",
                       "unit" : "sample.position_unit",
                       "storeas" : "float",
                       "attributes" : SASSAMPLE_POS_ATTR
                       }
    SASSAMPLE_POS_Z = {
                       "variable" : "{0}.sample.position.z = {1}",
                       "unit" : "sample.position_unit",
                       "storeas" : "float",
                       "attributes" : SASSAMPLE_POS_ATTR
                       }
    SASSAMPLE_POS = {
                     "children" : {
                                   "variable" : None,
                                   "x" : SASSAMPLE_POS_X,
                                   "y" : SASSAMPLE_POS_Y,
                                   "z" : SASSAMPLE_POS_Z,
                                   },
                     }
    SASSAMPLE_ORIENT_ATTR = {
                             "unit" : 
                             {
                              "variable" : \
                                    "{0}.sample.orientation_unit = \"{1}\"",
                              "storeas" : "content"
                              }
                             }
    SASSAMPLE_ORIENT_ROLL = {
                             "variable" : "{0}.sample.orientation.x = {1}",
                             "unit" : "sample.orientation_unit",
                             "storeas" : "float",
                             "attributes" : SASSAMPLE_ORIENT_ATTR
                             }
    SASSAMPLE_ORIENT_PITCH = {
                             "variable" : "{0}.sample.orientation.y = {1}",
                             "unit" : "sample.orientation_unit",
                             "storeas" : "float",
                             "attributes" : SASSAMPLE_ORIENT_ATTR
                             }
    SASSAMPLE_ORIENT_YAW = {
                             "variable" : "{0}.sample.orientation.z = {1}",
                             "unit" : "sample.orientation_unit",
                             "storeas" : "float",
                             "attributes" : SASSAMPLE_ORIENT_ATTR
                             }
    SASSAMPLE_ORIENT = {
                        "variable" : None,
                        "children" : {
                                      "roll" : SASSAMPLE_ORIENT_ROLL,
                                      "pitch" : SASSAMPLE_ORIENT_PITCH,
                                      "yaw" : SASSAMPLE_ORIENT_YAW,
                                      },
                        }
    SASSAMPLE = {
                 "attributes" : 
                    {"name" : {"variable" : "{0}.sample.name = \"{1}\""},},
                 "variable" : None,
                 "children" : {
                               "ID" : {"variable" : "{0}.sample.ID = \"{1}\""},
                               "thickness" : SASSAMPLE_THICK,
                               "transmission" : SASSAMPLE_TRANS, 
                               "temperature" : SASSAMPLE_TEMP, 
                               "position" : SASSAMPLE_POS,
                               "orientation" : SASSAMPLE_ORIENT,
                               "details" : {"variable" : \
                                        "{0}.sample.details.append(\"{1}\")"},
                               "<any>" : ANY
                               },
                 }
    SASINSTR_SRC_BEAMSIZE_ATTR = {
                                  "unit" : \
                                        "{0}.source.beam_size_unit = \"{1}\"",
                                  "storeas" : "content"
                                  }
    SASINSTR_SRC_BEAMSIZE_X = {
                               "variable" : "{0}.source.beam_size.x = {1}",
                               "unit" : "source.beam_size_unit",
                               "storeas" : "float",
                               "attributes" : SASINSTR_SRC_BEAMSIZE_ATTR
                               }
    SASINSTR_SRC_BEAMSIZE_Y = {
                               "variable" : "{0}.source.beam_size.y = {1}",
                               "unit" : "source.beam_size_unit",
                               "storeas" : "float",
                               "attributes" : SASINSTR_SRC_BEAMSIZE_ATTR
                               }
    SASINSTR_SRC_BEAMSIZE_Z = {
                               "variable" : "{0}.source.beam_size.z = {1}",
                               "unit" : "source.beam_size_unit",
                               "storeas" : "float",
                               "attributes" : SASINSTR_SRC_BEAMSIZE_ATTR
                               }
    SASINSTR_SRC_BEAMSIZE = {
                             "attributes" : 
                                {"name" : {"variable" : \
                                    "{0}.source.beam_size_name = \"{1}\""}},
                             "variable" : None,
                             "children" : {
                                           "x" : SASINSTR_SRC_BEAMSIZE_X,
                                           "y" : SASINSTR_SRC_BEAMSIZE_Y,
                                           "z" : SASINSTR_SRC_BEAMSIZE_Z,
                                           }
                             }
    SASINSTR_SRC_WL = {
                       "variable" : "{0}.source.wavelength = {1}",
                       "unit" : "source.wavelength_unit",
                       "storeas" : "float",
                       "attributes" : 
                       {
                        "unit" : 
                        {
                         "variable" : "{0}.source.wavelength_unit = \"{1}\"",
                         "storeas" : "content"
                         },
                        }
                       }
    SASINSTR_SRC_WL_MIN = {
                           "variable" : "{0}.source.wavelength_min = {1}",
                           "unit" : "source.wavelength_min_unit",
                           "storeas" : "float",
                           "attributes" : 
                           {
                            "unit" : 
                            {
                             "variable" : \
                                "{0}.source.wavelength_min_unit = \"{1}\"",  
                             "storeas" : "content"
                             },
                            }
                           }
    SASINSTR_SRC_WL_MAX = {
                           "variable" : "{0}.source.wavelength_max = {1}",
                           "unit" : "source.wavelength_max_unit",
                           "storeas" : "float",
                           "attributes" : 
                           {
                            "unit" : 
                            {
                             "variable" : \
                                "{0}.source.wavelength_max_unit = \"{1}\"",  
                             "storeas" : "content"
                             },
                            }
                           }
    SASINSTR_SRC_WL_SPR = {
                           "variable" : "{0}.source.wavelength_spread = {1}",
                           "unit" : "source.wavelength_spread_unit",
                           "storeas" : "float",
                           "attributes" : 
                           {
                            "unit" : 
                            {
                             "variable" : \
                                "{0}.source.wavelength_spread_unit = \"{1}\"",  
                             "storeas" : "content"
                             },
                            }
                           }
    SASINSTR_SRC = {
                    "attributes" : {"name" : {"variable" : \
                                              "{0}.source.name = \"{1}\""}},
                    "variable" : None,
                    "children" : {
                                  "radiation" : {"variable" : \
                                            "{0}.source.radiation = \"{1}\""},
                                  "beam_size" : SASINSTR_SRC_BEAMSIZE,
                                  "beam_shape" : {"variable" : \
                                            "{0}.source.beam_shape = \"{1}\""},
                                  "wavelength" : SASINSTR_SRC_WL,
                                  "wavelength_min" : SASINSTR_SRC_WL_MIN,
                                  "wavelength_max" : SASINSTR_SRC_WL_MAX,
                                  "wavelength_spread" : SASINSTR_SRC_WL_SPR,
                                  },
                    }
    SASINSTR_COLL_APER_ATTR = {
                               "unit" : {
                                         "variable" : "{0}.size_unit = \"{1}\"",
                                         "storeas" : "content"
                                         },                                    
                               }
    SASINSTR_COLL_APER_X = {
                            "variable" : "{0}.size.x = {1}",
                            "unit" : "size_unit",
                            "storeas" : "float",
                            "attributes" : SASINSTR_COLL_APER_ATTR
                            }
    SASINSTR_COLL_APER_Y = {
                            "variable" : "{0}.size.y = {1}",
                            "unit" : "size_unit",
                            "storeas" : "float",
                            "attributes" : SASINSTR_COLL_APER_ATTR
                            }
    SASINSTR_COLL_APER_Z = {
                            "variable" : "{0}.size.z = {1}",
                            "unit" : "size_unit",
                            "storeas" : "float",
                            "attributes" : SASINSTR_COLL_APER_ATTR
                            }
    SASINSTR_COLL_APER_SIZE = {
                               "attributes" : 
                               {"unit" : {"variable" : \
                                            "{0}.size_unit = \"{1}\""}},
                               "children" : {
                                             "storeas" : "float",
                                            "x" : SASINSTR_COLL_APER_X,
                                            "y" : SASINSTR_COLL_APER_Y,
                                            "z" : SASINSTR_COLL_APER_Z,
                                            }
                               }
    SASINSTR_COLL_APER_DIST = {
                               "storeas" : "float",
                               "attributes" : 
                               {
                                "storeas" : "content",
                                "unit" : {"variable" : \
                                            "{0}.distance_unit = \"{1}\""}
                                },
                               "variable" : "{0}.distance = {1}",
                               "unit" : "distance_unit",
                               }
    SASINSTR_COLL_APER = {
                          "variable" : None,
                          "attributes" : {
                                          "name" : {"variable" : \
                                                    "{0}.name = \"{1}\""},
                                          "type" : {"variable" : \
                                                    "{0}.type = \"{1}\""},
                                          },
                          "children" : {
                                        "size" : SASINSTR_COLL_APER_SIZE,
                                        "distance" : SASINSTR_COLL_APER_DIST
                                        }
                          }
    SASINSTR_COLL = {
                     "attributes" : 
                     {"name" : {"variable" : "{0}.name = \"{1}\""}},
                     "variable" : None,
                     "children" : 
                     {
                      "length" : 
                      {
                       "variable" : "{0}.length = {1}",
                       "unit" : "length_unit",
                       "storeas" : "float",
                       "attributes" : 
                       {
                        "storeas" : "content",
                        "unit" : {"variable" : "{0}.length_unit = \"{1}\""}
                        },
                       },
                      "aperture" : SASINSTR_COLL_APER,
                      },
                     }
    SASINSTR_DET_SDD = {
                        "variable" : "{0}.distance = {1}",
                        "unit" : "distance_unit",
                        "attributes" : 
                        {
                         "unit" : 
                         {
                          "variable" : "{0}.distance_unit = \"{1}\"",
                          "storeas" : "content"
                          }
                         },
                        }
    SASINSTR_DET_OFF_ATTR = {
                            "unit" : {
                                      "variable" : "{0}.offset_unit = \"{1}\"",
                                      "storeas" : "content"
                                      },
                            }
    SASINSTR_DET_OFF_X = {
                         "variable" : "{0}.offset.x = {1}",
                         "unit" : "offset_unit",
                         "attributes" : SASINSTR_DET_OFF_ATTR
                         }
    SASINSTR_DET_OFF_Y = {
                         "variable" : "{0}.offset.y = {1}",
                         "unit" : "offset_unit",
                         "attributes" : SASINSTR_DET_OFF_ATTR
                         }
    SASINSTR_DET_OFF_Z = {
                         "variable" : "{0}.offset.z = {1}",
                         "unit" : "offset_unit",
                         "attributes" : SASINSTR_DET_OFF_ATTR
                         }
    SASINSTR_DET_OFF = {
                        "variable" : None,
                        "children" : {
                                      "x" : SASINSTR_DET_OFF_X,
                                      "y" : SASINSTR_DET_OFF_Y,
                                      "z" : SASINSTR_DET_OFF_Z,
                                      }
                        }
    SASINSTR_DET_OR_ATTR = {
                            "unit" : "{0}.orientation_unit = \"{1}\"",
                            "storeas" : "content"
                            }
    SASINSTR_DET_OR_ROLL = {
                            "variable" : "{0}.orientation.x = {1}",
                            "unit" : "orientation_unit",
                            "attributes" : SASINSTR_DET_OR_ATTR
                            }
    SASINSTR_DET_OR_PITCH = {
                             "variable" : "{0}.orientation.y = {1}",
                             "unit" : "orientation_unit",
                             "attributes" : SASINSTR_DET_OR_ATTR
                             }
    SASINSTR_DET_OR_YAW = {
                           "variable" : "{0}.orientation.z = {1}",
                           "unit" : "orientation_unit",
                           "attributes" : SASINSTR_DET_OR_ATTR
                           }
    SASINSTR_DET_OR = {
                       "variable" : None,
                       "children" : {
                                     "roll" : SASINSTR_DET_OR_ROLL,
                                     "pitch" : SASINSTR_DET_OR_PITCH,
                                     "yaw" : SASINSTR_DET_OR_YAW,
                                     }
                       }
    SASINSTR_DET_BC_X = {
                         "variable" : "{0}.beam_center.x = {1}",
                         "unit" : "beam_center_unit",
                         "attributes" : 
                         {
                          "unit" : "{0}.beam_center_unit = \"{1}\"",
                          "storeas" : "content"
                          }
                         }
    SASINSTR_DET_BC_Y = {
                         "variable" : "{0}.beam_center.y = {1}",
                         "unit" : "beam_center_unit",
                         "attributes" : 
                         {
                          "unit" : "{0}.beam_center_unit = \"{1}\"",
                          "storeas" : "content"
                          }
                         }
    SASINSTR_DET_BC_Z = {
                         "variable" : "{0}.beam_center.z = {1}",
                         "unit" : "beam_center_unit",
                         "attributes" : 
                         {
                          "unit" : "{0}.beam_center_unit = \"{1}\"",
                          "storeas" : "content"
                          }
                         }
    SASINSTR_DET_BC = {
                       "variable" : None,
                       "children" : {
                                    "x" : SASINSTR_DET_BC_X,
                                    "y" : SASINSTR_DET_BC_Y,
                                    "z" : SASINSTR_DET_BC_Z,
                                    }
                      }
    SASINSTR_DET_PIXEL_X = {
                        "variable" : "{0}.pixel_size.x = {1}",
                        "unit" : "pixel_size_unit",
                        "attributes" : 
                        {
                         "unit" : "{0}.pixel_size_unit = \"{1}\"",
                         "storeas" : "content"
                         }
                        }
    SASINSTR_DET_PIXEL_Y = {
                        "variable" : "{0}.pixel_size.y = {1}",
                        "unit" : "pixel_size_unit",
                        "attributes" : 
                        {
                         "unit" : "{0}.pixel_size_unit = \"{1}\"",
                         "storeas" : "content"
                         }
                        }
    SASINSTR_DET_PIXEL_Z = {
                        "variable" : "{0}.pixel_size.z = {1}",
                        "unit" : "pixel_size_unit",
                        "attributes" : 
                        {
                         "unit" : "{0}.pixel_size_unit = \"{1}\"",
                         "storeas" : "content"
                         }
                        }
    SASINSTR_DET_PIXEL = {
                      "variable" : None,
                      "children" : {
                                    "x" : SASINSTR_DET_PIXEL_X,
                                    "y" : SASINSTR_DET_PIXEL_Y,
                                    "z" : SASINSTR_DET_PIXEL_Z,
                                    }
                      }
    SASINSTR_DET_SLIT = {
                         "variable" : "{0}.slit_length = {1}",
                         "unit" : "slit_length_unit",
                         "attributes" : 
                         {
                          "unit" : 
                          {
                           "variable" : "{0}.slit_length_unit = \"{1}\"",
                           "storeas" : "content"
                           }
                          }
                         }
    SASINSTR_DET = {
                    "storeas" : "float",
                    "variable" : None,
                    "attributes" : {
                                    "name" : 
                                    {
                                     "storeas" : "content",
                                     "variable" : "{0}.name = \"{1}\"",
                                     }
                                    },
                    "children" : {
                                  "name" : {
                                            "storeas" : "content",
                                            "variable" : "{0}.name = \"{1}\"",
                                            },
                                  "SDD" : SASINSTR_DET_SDD,
                                  "offset" : SASINSTR_DET_OFF,
                                  "orientation" : SASINSTR_DET_OR,
                                  "beam_center" : SASINSTR_DET_BC,
                                  "pixel_size" : SASINSTR_DET_PIXEL,
                                  "slit_length" : SASINSTR_DET_SLIT,
                                  }
                    }
    SASINSTR = {
                "variable" : None,
                "children" : 
                {
                 "variable" : None,
                 "name" : {"variable" : "{0}.instrument = \"{1}\""},
                 "SASsource" : SASINSTR_SRC,
                 "SAScollimation" : SASINSTR_COLL,
                 "SASdetector" : SASINSTR_DET,
                 },
                }
    CANSAS_FORMAT = {
                     "SASentry" : 
                     {
                      "units_optional" : True,
                      "variable" : None,
                      "storeas" : "content",
                      "attributes" : {"name" : {"variable" : \
                                    "{0}.run_name[node_value] = \"{1}\""}},
                      "children" : {
                                    "Title" : TITLE,
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


class CurrentLevel:
    """
    A helper class to hold information on where you are in the constants tree
    """
     
    current_level = ''
    ns_variable = ''
    ns_datatype = ''
    ns_optional = True
     
    def __init__(self):
        self.current_level = {}
        self.ns_variable = ''
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
