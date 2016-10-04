from oauth2client.service_account import ServiceAccountCredentials as SAC
from apiclient import discovery
from os.path import exists
import httplib2
import string


class Sheet(object):
    sac_file = 'google-sheets-key.json' # Service account credentials file


    def __init__(self, sheet_id):
        ''' Authenticate with a service account '''
        if not exists(self.sac_file):
            raise Exception('Need a service account file - check the TA slack channel for it')
        credentials = SAC.from_json_keyfile_name(self.sac_file,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        http = credentials.authorize(httplib2.Http())
        service = discovery.build('sheets', 'v4', http=http)
        self.sheet = service.spreadsheets().values()
        self.id = sheet_id


    def read(self, rows, cols, sheet=1):
        if type(cols[0]) is int:
            col1 = ''.join([string.ascii_uppercase[cols[0] % 26]] * (cols[0] / 26))
            col2 = ''.join([string.ascii_uppercase[cols[1] % 26]] * (cols[1] / 26))
        else: 
            col1, col2 = cols
        row1, row2 = rows
        ranges = 'Sheet%d!%s%d:%s%d' % (sheet, col1, row1, col2, row2)

        return self.sheet.get(spreadsheetId=self.id, 
                              range=ranges).execute().get('values', [])
    

    def write(self, data, sheet=1): 
        self.sheet.append(spreadsheetId=self.id, 
                          valueInputOption='RAW',
                          insertDataOption='INSERT_ROWS',
                          range='Sheet%s'%sheet, 
                          body={"values": data}).execute()


if __name__ == '__main__':
    spreadsheetId = '1Ed_tyOHhyc-BAPKkcXJRD_R5xZbbb93aPYxNQl8wYbg'

    data =  [
        ["test_name", "test_ta", "test_comment", "test_1", "test_2", "test_3", "test_4", "test_5", "test_6", "test_7", "test_8", '', 'test_notes'],
        ["test2_name", "test2_ta", "test2_comment", "test2_1", "tes2t_2", "test2_3", "test2_4", "test2_5", "test2_6", "test2_7", "test2_8", '', 'test2_notes'],
    ]
    sheet = Sheet(spreadsheetId)
    for row in sheet.read((1,5), ('A','M')):
        print row
    print

    sheet.write(data)

    for row in sheet.read((1,5), ('A','M')):
        print row
