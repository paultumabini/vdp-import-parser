import csv
import io
import os


class ImportSourcePipeline:
    def __init__(self, ftp=None, import_src=None):
        self._ftp = ftp
        self._import_src = import_src

    @classmethod
    def evaluate_src(cls, ftp, import_src):
        return cls(ftp, import_src)

    @staticmethod
    def process_item(*args, **kwargs):
        # logs
        logs = []
        total_dealers = 0

        for labels, data in kwargs.get('_import_src'):
            feed_id = labels.get('feed_id')
            dealer_name = labels.get('dealer_name')
            aim_id = labels.get('aim_id')

            fieldnames = data[0].keys()

            csvfile = io.StringIO()
            writer = csv.writer(csvfile)
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)

            file = f'VDP_URLS_{dealer_name}.csv'

            # store to ftp
            kwargs.get('_ftp').storbinary(f'STOR {file}', io.BytesIO(csvfile.getvalue().encode()))

            # save to DB
            # new vdp urls
            # if error, ignore and proceed
            try:
                for obj in data:
                    o = args[0](
                        dealer_id=aim_id,
                        dealer_vdpurl_feed_id=feed_id,
                        vin=obj.get('VIN'),
                        vehicle_url=obj.get('VDP URLS'),
                    )
                    o.save()
            except:
                pass

            # created source file
            vdp_src_file = args[1].objects.filter(vdpurl_feed_id=feed_id)
            for object in vdp_src_file:
                # add only if not yet availabe
                if not object.vdpurl_source_file:
                    object.vdpurl_source_file = file
                    object.save()

            # create logs
            total_dealers = total_dealers + 1
            logs.append(
                {
                    'FEEDID': feed_id,
                    'FILE': f'VDP_URLS_{dealer_name}.csv',
                    'AIMID': aim_id,
                }
            )

        print('File upload success!')
        print({f'{args[2].upper()} ({total_dealers})': logs})

    # save csv file
    @staticmethod
    def save_to_csv(*args, **kwargs):
        dir = '/home/pt/Dev/Projects/django/aim/vdp/output_csv/'
        # logs
        logs = []
        total_dealers = 0

        if not os.path.exists(dir):
            os.mkdir(dir)

        for labels, data in kwargs.get('_import_src'):
            dealer_name = labels.get('dealer_name')
            fieldnames = data[0].keys()

            with open(f'{dir}VDP_URLS_{args[0]}_{dealer_name}.csv', 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)

                # create logs
            total_dealers = total_dealers + 1
            logs.append(f'{total_dealers}. VDP_URLS_{dealer_name}.csv')

        print(f'[{args[0].upper()}] ({total_dealers}):', logs)
        print('Local csv files saved')
