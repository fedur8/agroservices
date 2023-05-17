# -*- python -*-
# -*- coding:utf-8 -*-
#
#       Copyright 2020 INRAE-CIRAD
#       Distributed under the Cecill-C License.
#       See https://cecill.info/licences/Licence_CeCILL-C_V1-en.html
#
# ==============================================================================


################## Interface Python IPM using Bioservice ########################################################

import json
from jsf import JSF
import datetime
from typing import Union
from pathlib import Path
from agroservices.services import REST
from agroservices.datadir import ipm_datadir

__all__ = ["IPM"]


class IPM(REST):
    """
    Interface to the IPM  https://ipmdecisions.nibio.no/

    .. doctest::
        >>> from agroservices.ipm import IPM
        >>> ipm = IPM()

        WeatherMetaDataService
        ----------------
        >>> ipm.get_parameter() 
        >>> ipm.get_qc() 
        >>> ipm.get_schema_weatherdata() 
        >>> ipm.post_schema_weatherdata_validate() 
        
        WeatherAdaptaterService
        ------------------------
        >>> ipm.get_weatheradapter()

        WeatherDataService
        ------------------
        >>> ipm.get_weatherdatasource()
        >>> ipm.post_weatherdatasource_location() 
        >>> ipm.get_weatherdatasource_location_point() 

        DSSService
        ----------
        >>> ipm.get_crop() 
        >>> ipm.get_dss() 
        >>> ipm.get_pest() 
        >>> ipm.post_dss_location() 
        >>> ipm.get_dssId() 
        >>> ipm.get_cropCode() 
        >>> ipm.get_dss_location_point() 
        >>> ipm.get_pestCode()
        >>> ipm.get_model()
        >>> ipm.get_input_schema() 

        DSSMetaDataService
        ---------------
        >>> ipm.get_schema_dss() 
        >>> dss.get_schema_fieldobservation() 
        >>> dss.get_schema_modeloutput() 
        >>> dss.post_schema_modeloutput_validate() 
        >>> ipm.post_schema_dss_yaml_validate() 
    """

    def __init__(self, name='IPM', url="https://platform.ipmdecisions.net", callback=None, *args, **kwargs):
        """Constructor

        Parameters
        ----------
        verbose : bool, optional
            set to False to prevent informative messages, by default False
        cache : bool, optional
            Use cache, by default False
        """
        # hack ipmdecisions.net is down
        url = 'https://ipmdecisions.nibio.no'
        super().__init__(
            name=name,
            url=url,
            *args, **kwargs)

        self.callback = callback  # use in all methods)

    ########################## MetaDataService ##########################################

    # Parameters
    def get_parameter(self) -> list:
        """Get a list of all the weather parameters defined in the platform

        Returns
        -------
        list
            weather parameters used in the platform
        """
        res = self.http_get(
            "api/wx/rest/parameter",
            frmt='json',
            headers=self.get_headers(content='json'),
            params={'callback': self.callback}
        )
        return res

    # QC
    def get_qc(self) -> list:
        """Get a list of QC code

        Returns
        -------
        list
            QC code used in plateform
        """
        res = self.http_get(
            "api/wx/rest/qc",
            frmt='json',
            headers=self.get_headers(content='json'),
            params={'callback': self.callback}
        )
        return res

    # schema weather data

    def get_schema_weatherdata(self) -> dict:
        """Get a schema that describes the IPM Decision platform's format for exchange of weather data

        Returns
        -------
        dict
            the schema that describes the IPM Decision platform's format for exchange of weather data
        """
        res = self.http_get(
            "api/wx/rest/schema/weatherdata",
            frmt='json',
            headers=self.get_headers(content='json'),
            params={'callback': self.callback}
        )
        return res

        # schema weather data validate

    def post_schema_weatherdata_validate(self, jsonfile: Union[str, Path] = 'weather_data.json') -> dict:
        """Validates the posted weather data against the Json schema

        Parameters
        ----------
        jsonfile : typing.Union[str,Path], optional
            weather data in json format, by default 'weather_data.json'

        Returns
        -------
        dict
            if the data is valid or not
        """
        with open(jsonfile) as json_file:
            data = json.load(json_file)

        res = self.http_post(
            "api/wx/rest/schema/weatherdata/validate",
            frmt='json',
            data=json.dumps(data),
            headers={"Content-Type": "application/json"}
        )
        return res

        ###################### WeatherAdaptaterService #############################

    def weatheradapter_forecast_params(self, source: dict,
                                       latitude: float = 67.2828,
                                       longitude: float = 14.3711,
                                       altitude: float = 0,
                                       interval: int = None,
                                       parameters: list = None,
                                       **options) -> dict:
        """Build a valid params dict for forecast data sources

        Parameters
        ----------
         source : dict
            A meta_data dict of the source (see self.get_weatherdatasource)
         interval : int,
             The measuring interval in seconds. Please note that the only allowed interval in this version is 3600 (hourly), by default 3600
         parameters : list,
             list of the requested weather parameters, by default the one listed under 'common'
         altitude : Union[int,float],
         latitude : Union[int,float],
            WGS84 Decimal degrees
         longitude : Union[int,float],
            WGS84 Decimal degrees
        """
        params = dict(latitude=latitude, longitude=longitude, altitude=altitude)

        if interval is None:
            interval = source['temporal']['intervals'][0]
        params.update({'interval': interval})

        if parameters is None:
            parameters = source['parameters']['common']
        params.update(dict(parameters=','.join(map(str, parameters))))

        if source['id'] == 'fi.fmi.forecast.location':
            params.pop('altitude')
        if source['id'] in ('dk.dmi.pointweather', 'se.slu.lantmet'):
            if 'timeStart' in options:
                start = datetime.datetime.fromisoformat('timeStart')
            else:
                start = datetime.datetime.today()
            timeStart = start.astimezone().isoformat()
            if 'timeEnd' in options:
                end = datetime.datetime.fromisoformat('timeEnd')
            else:
                end = start + datetime.timedelta(days=1)
            timeEnd = end.astimezone().isoformat()
            params.update(dict(timeStart=timeStart, timeEnd=timeEnd))

        return params

    def weatheradapter_observation_params(self, source,
                                          interval: int = None,
                                          parameters: list = None,
                                          timeStart: str = None,
                                          timeEnd: str = None,
                                          weatherStationId: int = None,
                                          **options):
        """Build a valid params dict for observation data sources

        Parameters
        ----------
         source : dict
            A meta_data dict of the source (see self.get_weatherdatasource)
         interval : int,
             The measuring interval in seconds. Please note that the only allowed interval in this version is 3600 (hourly), by default 3600
         parameters : list,
             list of the requested weather parameters, by default the one listed under 'common'
         timeStart : str,
             Start of weather data period (ISO-8601 Timestamp, e.g. 2020-06-12T00:00:00+03:00), by default to day (forecast) or first date available (historical)'
         timeEnd : str, optional
             End of weather data period (ISO-8601 Timestamp, e.g. 2020-07-03T00:00:00+03:00), by default tommorow (forecast) one day after first date (historical)
         weatherStationId : int,
             a location id
        """

        params = dict()

        if interval is None:
            interval = source['temporal']['intervals'][0]
        params.update({'interval': interval})

        if parameters is None:
            parameters = source['parameters']['common']
        params.update(dict(parameters=','.join(map(str, parameters))))

        if timeStart is None:
            start = datetime.datetime.fromisoformat(source['temporal']['historic']['start']) + datetime.timedelta(
                days=1)
            timeStart = start.astimezone().isoformat()
        if timeEnd is None:
            end = start + datetime.timedelta(days=1)
            timeEnd = end.astimezone().isoformat()
        params.update(dict(timeStart=timeStart, timeEnd=timeEnd))

        if weatherStationId is None:
            # test stations if geoJSon is not there
            if source['id'] == 'info.fruitweb':
                weatherStationId = 18150029
            elif source['id'] == 'net.ipmdecisions.metos':
                weatherStationId = 732
            else:
                features = source["spatial"]["geoJSON"]['features']
                if 'id' in features[0]:
                    weatherStationId = int(features[0]['id'])
                else:
                    weatherStationId = int(features[0]['properties']['id'])

        params.update(dict(weatherStationId=weatherStationId))

        # source-specific options
        if source['id'] == 'fi.fmi.observation.station':
            ignoreErrors = True
            if 'ignoreErrors' in options:
                ignoreErrors = options['ignoreErrors']
            params.update(dict(ignoreErrors=ignoreErrors))

        return params

    def weatheradapter_params(self, source, **kwargs):
        """Build a valid params dict for a given weatherdata source

        Parameters
        ----------
        source : dict
            A meta_data dict of the source (see self.get_weatherdatasource)

        Returns
        -------
        dict
            formated parameters dict
        """

        if source['access_type'] == 'stations':
            params = self.weatheradapter_observation_params(source, **kwargs)
        elif source['access_type'] == 'location':
            params = self.weatheradapter_forecast_params(source, **kwargs)
        else:
            raise ValueError("Unknown access type : " + source['access_type'])

        return params

    def get_weatheradapter(self, source: dict, params: dict = None, credentials: dict = None) -> dict:
        """Call weatheradapter service for a given weatherdata source

        Parameters
        ----------
        source : dict
            A meta_data dict of the source (see self.get_weatherdatasource)
        params : dict, optional
            a dict of formated parameters of the source weatheradapter service
            If None (default), use self.weatheradapter_params(source) to set some valid parameters
        credentials : dict, optional
            a dict of formated credential parameters


        Returns
        -------
        dict
            formated weather data (see self.get_schema_weatherdata)

        Raises
        ------
        ValueError
            datasource error: source_id is not referencing a valid datasource
        """

        if params is None:
            params = self.weatheradapter_params(source)

        endpoint = source['endpoint'].format(WEATHER_API_URL=self._url + '/api/wx')

        if not source['authentication_type'] == 'CREDENTIALS':
            res = self.http_get(endpoint, params=params, frmt='json')
        else:
            params['credentials'] = json.dumps(credentials)
            res = self.http_post(endpoint, data=params, frmt='json')

        return res

    ###################### WeatherDataService ##################################

    # weatherdatasource

    def get_weatherdatasource(self, source_id=None, access_type=None, authentication_type=None) -> list:
        """Access a dict of available wetherdata sources, of a source referenced by its id

        Parameters
        ----------
        source_id : str [optional]
            the id referencing the weatherdatasource (one  of the key of self.get_weatherdatasource)
        access_type : str [optional]
            Filter datasource that are different from access_type
        authentication_type : str [optional]
            Filter datasource that are different from authentication_type

        Returns
        -------
        dict
           wetherdata sources available on the platform if source_id is None
           The weatherdatatsource metadata referenced by source_id otherwise
        """
        res = self.http_get(
            "api/wx/rest/weatherdatasource",
            frmt='json',
            headers=self.get_headers(content='json'),
            params={'callback': self.callback}
        )

        for r in res:
            if 'geoJSON' in r['spatial']:
                if r['spatial']['geoJSON'] is not None:
                    r['spatial']['geoJSON'] = json.loads(r['spatial']['geoJSON'])

        sources = {item['id']: item for item in res}

        if source_id is None:
            res = sources
            if access_type is not None:
                res = {k: v for k, v in res.items() if v['access_type'] == access_type}
            if authentication_type is not None:
                res = {k: v for k, v in res.items() if v['authentication_type'] == authentication_type}
            return res
        elif source_id in sources:
            return sources[source_id]
        else:
            raise ValueError(
                "datasource error: source_id is not referencing a valid datasource: %s" % (','.join(sources.keys())))

    def post_weatherdatasource_location(
            self,
            tolerance: Union[int, float] = 0,
            geoJsonfile: Union[str, Path] = "GeoJson.json"
    ) -> list:
        """Search for weather data sources that serve the specific location. The location can by any valid Geometry, such as Point or Polygon. Example GeoJson input 

        Parameters
        ----------
        tolerance : Union[int,float], 
            Add some tolerance (in meters) to allow for e.g. a point to match the location of a weather station, by default 0
        geoJsonfile : Union[str,Path],
            GeoJson file, by default "GeoJson.json"

        Returns
        -------
        list
            A list of all the matching weather data sources
        """
        params = dict(
            callback=self.callback,
            tolerance=tolerance
        )

        with open(geoJsonfile) as json_file:
            data = json.load(json_file)

        res = self.http_post(
            "api/wx/rest/weatherdatasource/location",
            frmt='json',
            data=json.dumps(data),
            params=params,
            headers={"Content-Type": "application/json"}

        )

        return res

    def get_weatherdatasource_location_point(
            self,
            latitude: Union[str, float] = "59.678835236960765",
            longitude: Union[str, float] = "12.01629638671875",
            tolerance: int = 0
    ) -> list:
        """Search for weather data sources that serve the specific point.

        Parameters
        ----------
        latitude : Union[str,float],
            in decimal degrees (WGS84), by default "59.678835236960765"
        longitude : Union[str,float], 
            in decimal degrees (WGS84), by default "12.01629638671875"
        tolerance : int, 
            Add some tolerance (in meters) to allow for e.g. a point to match the location of a weather station, by default 0

        Returns
        -------
        list
            A list of all the matching weather data sources.
        """
        params = dict(
            callback=self.callback,
            latitude=latitude,
            longitude=longitude,
            tolerance=tolerance
        )

        res = self.http_get(
            "api/wx/rest/weatherdatasource/location/point",
            frmt='json',
            headers=self.get_headers(content='json'),
            params=params
        )

        return res

    ###########################   DSSService  ################################################

    def get_crop(self) -> list:
        """Get a list of EPPO codes for all crops that the DSS models in plateform

        Returns
        -------
        list
            A list of EPPO codes (https://www.eppo.int/RESOURCES/eppo_databases/eppo_codes) for all crops that the DSS models in the platform
        """
        res = self.http_get(
            "api/dss/rest/crop",
            frmt='json',
            headers=self.get_headers(content='json'),
            params={'callback': self.callback}
        )
        return res

    def get_dss(self) -> list:
        """Get a list all DSSs and models available in the platform

        Returns
        -------
        list
            a list all DSSs and models available in the platform
        """
        res = self.http_get(
            "api/dss/rest/dss",
            frmt='json',
            headers=self.get_headers(content='json'),
            params={'callback': self.callback}
        )
        return res

    def get_pest(self) -> list:
        """Get A list of EPPO codes https://www.eppo.int/RESOURCES/eppo_databases/eppo_codes) for all pests that the DSS models in the platform deals with in some way.

        Returns
        -------
        list
            A list of EPPO codes https://www.eppo.int/RESOURCES/eppo_databases/eppo_codes) for all pests that the DSS models in the platform deals with in some way.
        """
        res = self.http_get(
            "api/dss/rest/pest",
            frmt='json',
            headers=self.get_headers(content='json'),
            params={'callback': self.callback}
        )
        return res

    def post_dss_location(
            self,
            geoJsonfile: Union[str, Path] = "GeoJson.json") -> list:
        """Search for DSS models that have been validated for the specific location. The location can by any valid Geometry, such as Point or Polygon. Example geoJson input

        Parameters
        ----------
        geoJsonfile : Union[str,Path], optional
            GeoJson file, by default "GeoJson.json"

        Returns
        -------
        list
            A list of all the matching DSS models
        """
        with open(geoJsonfile) as json_file:
            data = json.load(json_file)

        res = self.http_post(
            "api/dss/rest/dss/location",
            frmt='json',
            data=json.dumps(data),
            headers={"Content-Type": "application/json"}
        )
        return res

    def get_dssId(
            self,
            DSSId: str = 'no.nibio.vips') -> dict:
        """Get all information about a specific DSS

        Parameters
        ----------
        DSSId : str, 
            id of the DSS, by default 'no.nibio.vips'

        Returns
        -------
        dict
            informations about a specific DSS
        """
        res = self.http_get(
            "api/dss/rest/dss/{}".format(DSSId),
            frmt='json'
        )

        return res

    def get_cropCode(
            self,
            cropCode: str = 'SOLTU') -> list:
        """Get all information about  DSS for a specific cropCode

        Parameters
        ----------
        cropCode : str, 
            EPPO cropcode <https://www.eppo.int/RESOURCES/eppo_databases/eppo_codes>, by default 'SOLTU'

        Returns
        -------
        list
            all informations about  DSS corresponding of cropCode
        """
        res = self.http_get(
            "api/dss/rest/dss/crop/{}".format(cropCode),
            frmt='json'
        )

        return res

    def get_dss_location_point(
            self,
            latitude: Union[float, str] = 59.678835236960765,
            longitude: Union[float, str] = 12.01629638671875
    ) -> list:
        """Search for models that are valid for the specific point

        Parameters
        ----------
        latitude : Union[float,str], optional
            decimal degrees (WGS84), by default 59.678835236960765
        longitude : Union[float,str], optional
            decimal degrees (WGS84), by default 12.01629638671875

        Returns
        -------
        list
            A list of all the matching DSS models
        """
        params = dict(
            callback=self.callback,
            latitude=latitude,
            longitude=longitude
        )

        res = self.http_get(
            "api/dss/rest/dss/location/point",
            frmt='json',
            headers=self.get_headers(content='json'),
            params=params
        )

        return res

    def get_pestCode(
            self,
            pestCode: str = 'PSILRO') -> list:
        """Get all information about  DSS for a specific pestCode

        Parameters
        ----------
        pestCode : str, optional
            EPPO code for the pest https://www.eppo.int/RESOURCES/eppo_databases/eppo_codes, by default 'PSILRO'

        Returns
        -------
        list
            list of DSS models that are applicable to the given pest
        """
        res = self.http_get(
            'api/dss/rest/dss/pest/{}'.format(pestCode),
            frmt='json'
        )

        return res

    def get_model(
            self,
            DSSId: str = 'no.nibio.vips',
            ModelId: str = 'PSILARTEMP') -> dict:
        """Get all information about a specific DSS model

        Parameters
        ----------
        DSSId : str, optional
            The id of the DSS containing the model, by default 'no.nibio.vips'
        ModelId : str, optional
            The id of the DSS model requested, by default 'PSILARTEMP'

        Returns
        -------
        dict
            All information of DSS model
        """
        res = self.http_get(
            "api/dss/rest/model/{}/{}".format(DSSId, ModelId),
            frmt='json'
        )
        if isinstance(res, dict):
            if 'execution' in res:
                if 'input_schema' in res['execution']:
                    res['execution']['input_schema'] = json.loads(res['execution']['input_schema'])

        return res

    def get_input_schema(
            self,
            DSSId: str = 'no.nibio.vips',
            ModelId: str = 'PSILARTEMP') -> dict:
        """Get the input Json schema for a specific DSS model

        Parameters
        ----------
        DSSId : str, optional
            The id of the DSS containing the model, by default 'no.nibio.vips'
        ModelId : str, optional
            The id of the DSS model requested, by default 'PSILARTEMP'

        Returns
        -------
        dict
            The inputs Json schema for the DSS model
        """
        res = self.http_get(
            "api/dss/rest/model/{}/{}/input_schema".format(DSSId, ModelId),
            frmt='json'
        )

        return res

    ###############################  DSSMetaDataService ##############################################

    def get_schema_dss(
            self) -> dict:
        """Provides schemas and validation thereof

        Returns
        -------
        dict
            Json schema of DSS
        """
        res = self.http_get(
            "api/dss/rest/schema/dss",
            frmt='json',
            headers=self.get_headers(content='json'),
            params={'callback': self.callback}
        )

        return res

    def get_schema_fieldobservation(
            self) -> dict:
        """Get the generic schema for field observations, containing the common properties for field observations. 
        These are location (GeoJson), time (ISO-8859 datetime), EPPO Code for the pest and crop. 
        In addition, quantification information must be provided. 
        This is specified in a custom schema, which must be a part of the input_schema property in the DSS model metadata. 

        Returns
        -------
        dict
            The generic schema for field observations
        """
        res = self.http_get(
            "api/dss/rest/schema/fieldobservation",
            frmt='json',
            headers=self.get_headers(content='json'),
            params={'callback': self.callback}
        )

        return res

    def get_schema_modeloutput(self) -> dict:
        """Get The Json Schema for the platform's standard for DSS model output

        Returns
        -------
        dict
            The Json Schema for the platform's standard for DSS model output
        """
        res = self.http_get(
            "api/dss/rest/schema/modeloutput",
            frmt='json',
            headers=self.get_headers(content='json'),
            params={'callback': self.callback}
        )

        return res

    def post_schema_modeloutput_validate(
            self,
            jsonfile: Union[str, Path] = 'modeloutput.json') -> dict:
        """Validate model output against this schema: https://ipmdecisions.nibio.no/api/dss/rest/schema/modeloutput

        Parameters
        ----------
        jsonfile : Union[str,Path], optional
            json file containing output model, by default 'modeloutput.json'

        Returns
        -------
        dict
            if the data is valid or not
        """
        with open(jsonfile) as json_file:
            data = json.load(json_file)

        res = self.http_post(
            "api/dss/rest/schema/modeloutput/validate",
            frmt='json',
            data=json.dumps(data),
            headers={"Content-Type": "application/json"}
        )

        return res

    def post_schema_dss_yaml_validate(
            self,
            yamlfile: Union[str, Path] = 'test_yaml_validate.yaml') -> dict:
        """Validate DSS YAML description file, using this Json schema: https://ipmdecisions.nibio.no/api/dss/rest/schema/dss

        Parameters
        ----------
        yamlfile : Union[str,Path], optional
            yaml file containing model description, by default 'test_yaml_validate.yaml'

        Returns
        -------
        dict
            if the data is valid or not
        """
        with open(yamlfile) as yaml_file:
            data = yaml.load(yaml_file, Loader=yaml.FullLoader)

        res = self.http_post(
            "api/dss/rest/schema/modeloutput/validate",
            frmt="json",
            data=yaml.dump(data),
            headers={"Content-Type": "application/json"}
        )

        return res

    ###############################  Run model ##############################################

    def write_weatherdata_schema(self):
        schema = self.get_schema_weatherdata()
        json_object = json.dumps(schema, indent=4)
        with open(ipm_datadir + "schema_weatherdata.json", "w") as outfile:
            outfile.write(json_object)

    def write_fieldobservation_schema(self):
        schema = self.get_schema_fieldobservation()

        json_object = json.dumps(schema, indent=4)
        with open(ipm_datadir + "schema_fieldobservation.json", "w") as outfile:
            outfile.write(json_object)

    def model_input(self,
                    model: dict,
                    parameters: dict = None,
                    weather_data: dict = None,
                    field_observations: dict = None,
                    field_observation_quantifications: dict = None):
        """Build model_input dict required bu run_model service"""

        schema = model['execution']['input_schema'].copy()
        config_params = schema['properties']['configParameters']
        fieldobs = ('fieldObservations', 'fieldObservationQuantifications')

        # fill externaly defined refs
        if 'weatherData' in schema['properties']:
            schema['properties']['weatherData'] = {'type': 'string', 'pattern': '^{WEATHER_DATA}$',
                                                   'default': '{WEATHER_DATA}'}
        for p in fieldobs:
            if p in config_params['properties']:
                config_params['properties'][p] = {'type': 'string', 'pattern': '^{'+p+'}$',
                                                     'default': '{'+p+'}'}
        # pop definitions to minimize bugs [some are buggy, eg PSILAROBE miss 'type'='object' and make parser fail
        if 'definitions' in schema:
            schema.pop('definitions')

        faker = JSF(schema)
        input = faker.generate()

        # fill with default or parameters if any
        if parameters is None:
            parameters = {}
        if 'configParameters' in input:
            for p in input['configParameters']:
                if p in parameters:
                    input['configParameters'][p] = parameters[p]
                elif 'default' in config_params['properties'][p]:
                    input['configParameters'][p] = config_params['properties'][p]['default']
                else:
                    pass

        # add Data
        required = []
        interval = None
        if model['input']['weather_parameters'] is not None:
            required = [item['parameter_code'] for item in model['input']['weather_parameters']]
            interval = model['input']['weather_parameters'][0]['interval']
        if 'weatherData' in input:
            if weather_data is None:
                raise ValueError(model['id'] + ' requires WeatherData as input')
            assert all(code in weather_data['weatherParameters'] for code in required), "WeatherData parameter are missing: " + str(set(required) - set(weather_data['weatherParameters']))
            assert interval == weather_data['interval'], 'weatherdata interval is not fullfilling model requirements'
            input['weatherData'] = weather_data
        elif weather_data is not None:
            if 'weatherData' in schema['properties']:
                assert all(code in weather_data['weatherParameters'] for code in required), "Some weatherdata parameter are missing"+ str(set(required) - set(weather_data['weatherParameters']))
                assert interval == weather_data['interval'], 'weatherdata interval is not fullfilling model requirements'
                input['weatherData'] = weather_data
        for p, pvalue in zip(fieldobs,
                             [field_observations, field_observation_quantifications]):
            if p in input['configParameters']:
                if pvalue is None:
                    raise ValueError(model['id'] + ' requires ' + p + ' as input')
                input['configParameters'][p] = pvalue
            elif pvalue is not None:
                if p in config_params['properties']:
                    input['configParameters'][p] = pvalue
        return input


    def run_model(
            self,
            model: dict,
            parameters: dict = None,
            weather_data: dict = None,
            field_observations: dict = None,
            field_observation_quantifications: dict = None,
            model_input: dict = None):
        """Run Dss Model and get output

        Parameters
        ----------
        model : dict
            The model meta_data dict (see self.get_model)
        parameters : dict [optional]
            Model parameters, as defined in model input schema (see model['execution']['input_schema'])
        weather_data: dict [optional]
            Weather data to feed the model (see self.get_weatheradapter)
        field_observations: dict [optional]
            Dict of observation location / time of observation, as defined in IPM (see self.get_schema_fieldobservation)
        field_observation_quantifications: dict [optional]
            Dict of obseration data, as defined in model input schema. (see model['execution']['input_schema']
        model_input : dict, optional
            A dict with all inputs as defined in model input schema (see model['execution']['input_schema']

        Returns
        -------
        dict
            output of model
        """
        if model_input is None:
            model_input = self.model_input(model, parameters=parameters,
                                           weather_data=weather_data,
                                           field_observations=field_observations,
                                           field_observation_quantifications=field_observation_quantifications)

        endpoint = model['execution']['endpoint']

        res = self.http_post(
            endpoint,
            frmt='json',
            data=json.dumps(model_input),
            headers={"Content-Type": "application/json"}
        )

        return res
