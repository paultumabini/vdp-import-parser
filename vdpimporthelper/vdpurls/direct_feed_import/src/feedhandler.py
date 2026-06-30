import re
import logging
from typing import Any, Dict, List, Optional

import pandas as pd
import xmltodict

logger = logging.getLogger(__name__)


class FeedHandler:
    """Parse source feeds into normalized records for pipeline ingestion.

    All parser methods are stateless classmethods and safe to call concurrently.
    """

    @classmethod
    def create_data_list(
        cls, dataframe: pd.DataFrame, **kwargs: Any
    ) -> List[List[Any]]:
        fields: List[str] = kwargs.get('fields', [])
        # If no fields were configured, there's no identifier column to
        # filter on and no target columns to select - treat both as empty/
        # absent rather than unpacking a placeholder [None] into a
        # List[str]-typed variable (which is what caused the mypy error).
        # This also fixes a latent runtime bug: the original
        # `identifier, *vdp_fields = kwargs.get('fields', [])` would have
        # raised "not enough values to unpack" if fields was ever empty.
        if fields:
            identifier: Optional[str] = fields[0]
            vdp_fields: List[str] = fields[1:]
        else:
            identifier = None
            vdp_fields = []
        dict_data_list: List[List[Any]] = []

        for feed_id in kwargs.get('feed_ids', []):
            # .copy() ensures each iteration (and each concurrent call to this
            # method from another thread) works on its own DataFrame and
            # never mutates a shared one.
            df = dataframe.copy()
            if kwargs.get('type') == 'batch' and identifier:
                df = df[df[identifier] == feed_id]

            if df.empty or len(vdp_fields) < 3:
                continue

            # Normalize headers before selecting target columns.
            df.columns = df.columns.str.strip()
            # .loc keeps the selection typed as DataFrame (list indexing can
            # look like ndarray to pyright/pandas-stubs).
            vdp_urls: pd.DataFrame = df.loc[:, vdp_fields].rename(
                columns={
                    vdp_fields[0]: 'dealer_name',
                    vdp_fields[1]: 'VIN',
                    vdp_fields[2]: 'VDP URLS',
                }
            )
            data = vdp_urls.to_dict('records')
            if not data:
                continue

            dealer_name = data[0].get('dealer_name')
            filtered_list = [
                {k: v for k, v in row.items() if k != 'dealer_name'} for row in data
            ]

            model = kwargs['model']
            # Read-only ORM query - safe to run concurrently across threads.
            vdp_setup = model.objects.filter(vdpurl_feed_id__icontains=feed_id).first()
            aim_id = vdp_setup.dealer_id if vdp_setup else None

            dealername = (
                re.sub('[^A-Za-z0-9]+', '', dealer_name).lower()
                if dealer_name
                else None
            )

            dict_data_list.append(
                [
                    {'feed_id': feed_id, 'dealer_name': dealername, 'aim_id': aim_id},
                    filtered_list,
                ]
            )

        return dict_data_list

    @classmethod
    def parse_csv(cls, **kwargs: Any) -> List[List[Any]]:
        try:
            dframe = pd.read_csv(kwargs['raw'], encoding='cp850')
            return cls.create_data_list(dframe, **kwargs)
        except UnicodeDecodeError as err:
            logger.error('Unable to decode CSV source: %s', err)
            return []

    @classmethod
    def parse_xml_edealer(cls, **kwargs: Any) -> List[List[Any]]:
        data = xmltodict.parse(kwargs['raw'].getvalue())
        dealers = data.get('Datafeed', {}).get('Dealership', [])

        if isinstance(dealers, dict):
            dealers = [dealers]

        xmldata: List[List[Any]] = []
        for dealer in dealers:
            for feed_id in kwargs.get('feed_ids', []):
                if dealer.get('Dealership_ID') != feed_id:
                    continue

                dealer_name: Optional[str] = dealer.get('Dealer_Name')
                vehicle_data = dealer.get('Inventory', {}).get('Vehicle', {})

                def item_row(
                    source_dealer: Dict[str, Any],
                    name: Optional[str],
                    vehicle: Dict[str, Any],
                ) -> List[Any]:
                    return [
                        source_dealer.get('Dealership_ID'),
                        re.sub('[^A-Za-z0-9]+', '', name).lower() if name else None,
                        vehicle.get('VIN'),
                        vehicle.get('Inventory_VDP_URL'),
                    ]

                if isinstance(vehicle_data, dict):
                    xmldata.append(item_row(dealer, dealer_name, vehicle_data))
                elif isinstance(vehicle_data, list):
                    for vehicle in vehicle_data:
                        xmldata.append(item_row(dealer, dealer_name, vehicle))

        dframe = pd.DataFrame(xmldata, columns=kwargs.get('fields', []))
        return cls.create_data_list(dframe, **kwargs)

    @classmethod
    def parse_csv_insert_dname(cls, **kwargs: Any) -> List[List[Any]]:
        try:
            dframe = pd.read_csv(kwargs['raw'], encoding='cp850')
            dict_df = dframe.to_dict('records')
            list_data = [
                dict(
                    zip(
                        kwargs['fields'],
                        [
                            data.get(''),
                            'ffuncars',
                            data.get('SERIALNUMBER'),
                            data.get('VEHICLE_URL'),
                        ],
                    )
                )
                for data in dict_df
            ]
            df_data = pd.DataFrame(list_data)
            return cls.create_data_list(df_data, **kwargs)
        except UnicodeDecodeError as err:
            logger.error(
                'Unable to decode CSV source with insert_dname parser: %s', err
            )
            return []
