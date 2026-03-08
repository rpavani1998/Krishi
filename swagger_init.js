
window.onload = function() {
  // Build a system
  var url = window.location.search.match(/url=([^&]+)/);
  if (url && url.length > 1) {
    url = decodeURIComponent(url[1]);
  } else {
    url = window.location.origin;
  }
  var options = {
  "swaggerDoc": {
    "openapi": "3.0.0",
    "info": {
      "title": "CEDA API",
      "version": "1.0.0",
      "description": "API documentation for the datasets provided by CEDA. Currently serving only Agmarknet data."
    },
    "servers": [
      {
        "url": "https://api.ceda.ashoka.edu.in/v1",
        "description": "Production server"
      }
    ],
    "components": {
      "securitySchemes": {
        "bearerAuth": {
          "type": "http",
          "scheme": "bearer",
          "bearerFormat": "JWT"
        }
      }
    },
    "tags": [
      {
        "name": "Agmarknet",
        "description": "APIs to programmatically access the Agmarknet data"
      }
    ],
    "paths": {
      "/agmarknet/commodities": {
        "get": {
          "tags": [
            "Agmarknet"
          ],
          "summary": "Obtain the list of all commodities from the agmarknet platform",
          "security": [
            {
              "bearerAuth": []
            }
          ],
          "responses": {
            "200": {
              "description": "List of commodities",
              "content": {
                "application/json": {
                  "schema": {
                    "type": "object",
                    "properties": {
                      "commodities": {
                        "type": "array",
                        "items": {
                          "type": "object",
                          "properties": {
                            "id": {
                              "type": "integer"
                            },
                            "name": {
                              "type": "string"
                            }
                          }
                        }
                      }
                    }
                  }
                }
              }
            },
            "401": {
              "description": "Unauthorized (invalid or missing API token)"
            },
            "429": {
              "description": "Too many requests (rate limit exceeded)"
            },
            "500": {
              "description": "Internal server error"
            }
          }
        }
      },
      "/agmarknet/geographies": {
        "get": {
          "tags": [
            "Agmarknet"
          ],
          "summary": "Obtain the list of all states and districts available.",
          "security": [
            {
              "bearerAuth": []
            }
          ],
          "responses": {
            "200": {
              "description": "List of geographies for the commodity",
              "content": {
                "application/json": {
                  "schema": {
                    "type": "object",
                    "properties": {
                      "geographies": {
                        "type": "array",
                        "items": {
                          "type": "object",
                          "properties": {
                            "state_id": {
                              "type": "integer"
                            },
                            "state_name": {
                              "type": "string"
                            },
                            "districts": {
                              "type": "array",
                              "items": {
                                "type": "object",
                                "properties": {
                                  "district_id": {
                                    "type": "integer"
                                  },
                                  "district_name": {
                                    "type": "string"
                                  }
                                }
                              }
                            }
                          }
                        }
                      }
                    }
                  }
                }
              }
            },
            "400": {
              "description": "Missing or invalid commodity_id"
            },
            "401": {
              "description": "Unauthorized (invalid or missing API token)"
            },
            "429": {
              "description": "Too many requests (rate limit exceeded)"
            },
            "500": {
              "description": "Internal server error"
            }
          }
        }
      },
      "/agmarknet/markets": {
        "post": {
          "tags": [
            "Agmarknet"
          ],
          "summary": "Obtain the list of markets for a given commodity, state and district.",
          "security": [
            {
              "bearerAuth": []
            }
          ],
          "requestBody": {
            "required": true,
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "commodity_id": {
                      "type": "integer",
                      "description": "Commodity ID (required). List can be obtained from /commodities endpoint."
                    },
                    "state_id": {
                      "type": "integer",
                      "description": "State ID (required). List can be obtained from /geographies endpoint."
                    },
                    "district_id": {
                      "type": "integer",
                      "description": "District ID (required). List can be obtained from /geographies endpoint."
                    },
                    "indicator": {
                      "type": "string",
                      "enum": [
                        "price",
                        "quantity"
                      ],
                      "description": "Indicator type (required, must be 'price' or 'quantity')"
                    }
                  },
                  "required": [
                    "commodity_id",
                    "state_id",
                    "district_id",
                    "indicator"
                  ],
                  "example": {
                    "commodity_id": 3,
                    "state_id": 3,
                    "district_id": 41,
                    "indicator": "price"
                  }
                }
              }
            }
          },
          "responses": {
            "200": {
              "description": "List of markets for the given parameters",
              "content": {
                "application/json": {
                  "schema": {
                    "type": "object",
                    "properties": {
                      "data": {
                        "type": "array",
                        "items": {
                          "type": "object",
                          "properties": {
                            "census_state_id": {
                              "type": "integer"
                            },
                            "census_district_id": {
                              "type": "integer"
                            },
                            "market_id": {
                              "type": "integer"
                            },
                            "market_name": {
                              "type": "string"
                            }
                          }
                        }
                      }
                    }
                  }
                }
              }
            },
            "400": {
              "description": "Invalid or missing parameters"
            },
            "401": {
              "description": "Unauthorized (invalid or missing API token)"
            },
            "429": {
              "description": "Too many requests (rate limit exceeded)"
            },
            "500": {
              "description": "Internal server error"
            }
          }
        }
      },
      "/agmarknet/prices": {
        "post": {
          "tags": [
            "Agmarknet"
          ],
          "summary": "Obtain the prices for a commodity at the national, state, district or the market level.",
          "security": [
            {
              "bearerAuth": []
            }
          ],
          "requestBody": {
            "required": true,
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "commodity_id": {
                      "type": "integer",
                      "description": "Commodity ID (required)"
                    },
                    "state_id": {
                      "type": "integer",
                      "description": "State ID (required). Use 0 for all India level data or state level integer value obtained from /geographies"
                    },
                    "district_id": {
                      "type": "array",
                      "items": {
                        "type": "integer"
                      },
                      "description": "Optional district IDs. If not provided, will fetch data at the national or the state level. If provided, will fetch data at the district level."
                    },
                    "market_id": {
                      "type": "array",
                      "items": {
                        "type": "integer"
                      },
                      "description": "Optional market IDs. If not provided, will fetch data directly at the district level. If provided, will fetch data for the particular markets within that district."
                    },
                    "from_date": {
                      "type": "string",
                      "format": "date",
                      "description": "Start date (required)"
                    },
                    "to_date": {
                      "type": "string",
                      "format": "date",
                      "description": "End date (required)"
                    }
                  },
                  "required": [
                    "commodity_id",
                    "state_id",
                    "from_date",
                    "to_date"
                  ],
                  "example": {
                    "commodity_id": 1,
                    "state_id": 8,
                    "district_id": [
                      104
                    ],
                    "market_id": [
                      255,
                      3149
                    ],
                    "from_date": "2025-03-01",
                    "to_date": "2025-06-01"
                  }
                }
              }
            }
          },
          "responses": {
            "200": {
              "description": "List of price records for the given filters",
              "content": {
                "application/json": {
                  "schema": {
                    "type": "object",
                    "properties": {
                      "data": {
                        "type": "array",
                        "items": {
                          "type": "object",
                          "properties": {
                            "date": {
                              "type": "string",
                              "format": "date"
                            },
                            "commodity_id": {
                              "type": "integer"
                            },
                            "census_state_id": {
                              "type": "integer"
                            },
                            "census_district_id": {
                              "type": "integer"
                            },
                            "market_id": {
                              "type": "integer"
                            },
                            "min_price": {
                              "type": "number"
                            },
                            "max_price": {
                              "type": "number"
                            },
                            "modal_price": {
                              "type": "number"
                            }
                          }
                        }
                      }
                    }
                  }
                }
              }
            },
            "400": {
              "description": "Missing or invalid required parameters"
            },
            "401": {
              "description": "Unauthorized (invalid or missing API token)"
            },
            "429": {
              "description": "Too many requests (rate limit exceeded)"
            },
            "500": {
              "description": "Internal server error"
            }
          }
        }
      },
      "/agmarknet/quantities": {
        "post": {
          "tags": [
            "Agmarknet"
          ],
          "summary": "Obtain the quantities for a commodity at the national, state, district or market level.",
          "security": [
            {
              "bearerAuth": []
            }
          ],
          "requestBody": {
            "required": true,
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "commodity_id": {
                      "type": "integer",
                      "description": "Commodity ID (required)"
                    },
                    "state_id": {
                      "type": "integer",
                      "description": "State ID (required). Use 0 for all India level data or state level integer value obtained from /geographies"
                    },
                    "district_id": {
                      "type": "array",
                      "items": {
                        "type": "integer"
                      },
                      "description": "Optional district IDs. If not provided, will fetch data at the national or the state level. If provided, will fetch data at the district level."
                    },
                    "market_id": {
                      "type": "array",
                      "items": {
                        "type": "integer"
                      },
                      "description": "Optional market IDs. If not provided, will fetch data directly at the district level. If provided, will fetch data for the particular markets within that district."
                    },
                    "from_date": {
                      "type": "string",
                      "format": "date",
                      "description": "Start date (required)"
                    },
                    "to_date": {
                      "type": "string",
                      "format": "date",
                      "description": "End date (required)"
                    }
                  },
                  "required": [
                    "commodity_id",
                    "state_id",
                    "from_date",
                    "to_date"
                  ],
                  "example": {
                    "commodity_id": 3,
                    "state_id": 3,
                    "district_id": [
                      43
                    ],
                    "market_id": [
                      232
                    ],
                    "from_date": "2014-01-01",
                    "to_date": "2015-01-01"
                  }
                }
              }
            }
          },
          "responses": {
            "200": {
              "description": "List of quantity records for the given filters",
              "content": {
                "application/json": {
                  "schema": {
                    "type": "object",
                    "properties": {
                      "data": {
                        "type": "array",
                        "items": {
                          "type": "object",
                          "properties": {
                            "date": {
                              "type": "string",
                              "format": "date"
                            },
                            "commodity_id": {
                              "type": "integer"
                            },
                            "census_state_id": {
                              "type": "integer"
                            },
                            "census_district_id": {
                              "type": "integer"
                            },
                            "market_id": {
                              "type": "integer"
                            },
                            "quantity": {
                              "type": "number"
                            }
                          }
                        }
                      }
                    }
                  }
                }
              }
            },
            "400": {
              "description": "Missing or invalid required parameters"
            },
            "401": {
              "description": "Unauthorized (invalid or missing API token)"
            },
            "429": {
              "description": "Too many requests (rate limit exceeded)"
            },
            "500": {
              "description": "Internal server error"
            }
          }
        }
      }
    }
  },
  "customOptions": {}
};
  url = options.swaggerUrl || url
  var urls = options.swaggerUrls
  var customOptions = options.customOptions
  var spec1 = options.swaggerDoc
  var swaggerOptions = {
    spec: spec1,
    url: url,
    urls: urls,
    dom_id: '#swagger-ui',
    deepLinking: true,
    presets: [
      SwaggerUIBundle.presets.apis,
      SwaggerUIStandalonePreset
    ],
    plugins: [
      SwaggerUIBundle.plugins.DownloadUrl
    ],
    layout: "StandaloneLayout"
  }
  for (var attrname in customOptions) {
    swaggerOptions[attrname] = customOptions[attrname];
  }
  var ui = SwaggerUIBundle(swaggerOptions)

  if (customOptions.oauth) {
    ui.initOAuth(customOptions.oauth)
  }

  if (customOptions.preauthorizeApiKey) {
    const key = customOptions.preauthorizeApiKey.authDefinitionKey;
    const value = customOptions.preauthorizeApiKey.apiKeyValue;
    if (!!key && !!value) {
      const pid = setInterval(() => {
        const authorized = ui.preauthorizeApiKey(key, value);
        if(!!authorized) clearInterval(pid);
      }, 500)

    }
  }

  if (customOptions.authAction) {
    ui.authActions.authorize(customOptions.authAction)
  }

  window.ui = ui
}
