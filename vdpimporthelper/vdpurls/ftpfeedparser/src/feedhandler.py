import re
from typing import Any, Dict, List, Union

import pandas as pd
import xmltodict

# from functools import reduce


class FeedHandler:
    """
    Using `getattr(foo, 'bar')`, add @classmethod to avoid :
    `TypeError: <class_method> missing 1 required positional argument: 'self'`
    """

    @classmethod
    def create_data_list(
        cls, *args: Any, **kwargs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        id, *vdp = kwargs.get('fields')
        dict_data_list = []

        """ list of dealer feed ids to create df when matched """
        for feed_id in kwargs['feed_ids']:
            df = args[0]

            # if batch file, define, otherwise, proceed renaming columns for single feed
            if kwargs['type'] == 'batch':
                mask = df[id] == feed_id
                df = df[mask]

            # select cols for dealer_names,vin & vdp urls
            # rename cols names for consistency
            vdp_urls = df[vdp].rename(
                columns={
                    f'{vdp[0]}': 'dealer_name',
                    f'{vdp[1]}': 'VIN',
                    f'{vdp[2]}': 'VDP URLS',
                }
            )

            data = vdp_urls.to_dict('records')

            # filtered `truthy` list
            if bool(data):
                dealer_name = data[0].get('dealer_name')

                # filter out dealer_name key value pair from list
                filtered_list = [
                    {k: v for k, v in d.items() if k != 'dealer_name'} for d in data
                ]

                try:
                    # get() methods throws `MultipleObjectsReturned` error
                    aim_id = (
                        kwargs['model']
                        .objects.filter(vdpurl_feed_id__icontains=feed_id)
                        .first()
                        .dealer_id
                    )
                except kwargs['model'].DoesNotExist:
                    aim_id = None

                dealername = (
                    re.sub('[^A-Za-z0-9]+', '', dealer_name).lower()
                    if dealer_name
                    else None
                )

                dict_data_list.append(
                    [
                        {
                            'feed_id': feed_id,
                            'dealer_name': dealername,
                            'aim_id': aim_id,
                        },
                        filtered_list,
                    ]
                )

        return dict_data_list

    @classmethod
    def parse_csv(
        cls, **kwargs: Dict[str, Union[str, pd.DataFrame]]
    ) -> List[Dict[str, Any]]:
        # Create the pandas DataFrame
        try:
            # encoding types: ('cp1252', 'cp850','utf-8','utf8')
            dframe = pd.read_csv(kwargs['raw'], encoding='cp850')
            return cls.create_data_list(dframe, **kwargs)
        except UnicodeDecodeError as err:
            print('ERROR', err)

    @classmethod
    def parse_xml_edealer(
        cls, **kwargs: Dict[str, Union[str, pd.DataFrame]]
    ) -> List[Dict[str, Any]]:
        data = xmltodict.parse(kwargs['raw'].getvalue())
        dealers = data.get('Datafeed').get('Dealership')

        xmldata = []
        for dealer in dealers:
            for id in kwargs['feed_ids']:
                if dealer.get('Dealership_ID') == id:
                    dealer_name = dealer.get('Dealer_Name')
                    vehicle_data = dealer.get('Inventory', {}).get('Vehicle', {})

                    """ evaluate vdp data of dict or list """

                    def instance_item(d, d_name, v_data):
                        return [
                            d.get('Dealership_ID'),
                            re.sub('[^A-Za-z0-9]+', '', d_name).lower(),
                            v_data.get('VIN'),
                            v_data.get('Inventory_VDP_URL'),
                        ]

                    if isinstance(vehicle_data, dict):
                        xmldata.append(
                            [*instance_item(dealer, dealer_name, vehicle_data)]
                        )

                    if isinstance(vehicle_data, list):
                        for v_data in vehicle_data:
                            xmldata.append(
                                [*instance_item(dealer, dealer_name, v_data)]
                            )

        # Create the pandas DataFrame
        # arg1: two dimentional data lists --> [[],[],...], arg2: header's name
        dframe = pd.DataFrame(xmldata, columns=kwargs['fields'])

        return cls.create_data_list(dframe, **kwargs)

    # Temporary individual functions:
    @classmethod
    def parse_csv_insert_dname(
        cls, **kwargs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        try:
            dframe = pd.read_csv(kwargs['raw'], encoding='cp850')
            # convert dframe data to list of dictionaries
            dict_df = dframe.to_dict('records')

            list_data = [
                dict(
                    zip(
                        kwargs['fields'],
                        [
                            data.get('dealer_id'),
                            'cmhniagara',
                            data.get('vin'),
                            data.get('misc_1'),
                        ],
                    )
                )
                for data in dict_df
            ]

            # convert list of dictionaries to dataframe
            df_data = pd.DataFrame(list_data)

            return cls.create_data_list(df_data, **kwargs)
        except UnicodeDecodeError as err:
            print('ERROR', err)
