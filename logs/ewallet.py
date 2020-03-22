    Starting var:.. self = <base.res_user.ResUser object at 0xb6b9516c>
    Starting var:.. kwargs = {'ctype': 'event', 'event': 'request', 'request'...st': 4.36, 'notes': 'Test Notes - Action Supply'}
    00:18:48.554145 call       638     def handle_user_event_request_credits(self, **kwargs):
    00:18:48.555054 line       639         log.debug('')
    00:18:48.555959 line       640         if not kwargs.get('partner_account'):
    00:18:48.556179 line       644         _local_credit_wallet = self.fetch_user_credit_wallet()
    New var:....... _local_credit_wallet = <base.credit_wallet.CreditEWallet object at 0xb6b8c04c>
    00:18:48.562831 line       645         _remote_credit_wallet = kwargs['partner_account'].fetch_user_credit_wallet()
    New var:....... _remote_credit_wallet = <base.credit_wallet.CreditEWallet object at 0xb6b8c04c>
    00:18:48.563552 line       647         if not _remote_credit_wallet:
    00:18:48.563706 line       654         _extract_credits_from_local = self.action_extract_credits_from_wallet(**kwargs)
        Starting var:.. self = <base.res_user.ResUser object at 0xb6b9516c>
        Starting var:.. kwargs = {'ctype': 'event', 'event': 'request', 'request'...st': 4.36, 'notes': 'Test Notes - Action Supply'}
        00:18:48.563985 call       611     def action_extract_credits_from_wallet(self, **kwargs):
        00:18:48.564125 line       612         log.debug('')
        00:18:48.564617 line       613         _credit_wallet = kwargs.get('credit_wallet') or \
        00:18:48.564768 line       614                 self.fetch_user_credit_wallet()
        New var:....... _credit_wallet = <base.credit_wallet.CreditEWallet object at 0xb6b8c04c>
        00:18:48.565535 line       615         if not _credit_wallet:
        00:18:48.565733 line       617         _extract = _credit_wallet.main_controller(
        00:18:48.565875 line       618                 controller='system', action='extract',
        00:18:48.566052 line       619                 credits=kwargs.get('credits') or 0
        New var:....... _extract = -10
        00:18:48.568171 line       621         return True if _extract else False
        00:18:48.568400 return     621         return True if _extract else False
        Return value:.. True
    New var:....... _extract_credits_from_local = True
    00:18:48.568896 line       655         _supply_credits_to_remote = kwargs['partner_account'].action_supply_credits_to_wallet(**kwargs)
        Starting var:.. self = <base.res_user.ResUser object at 0xb6b9516c>
        Starting var:.. kwargs = {'ctype': 'event', 'event': 'request', 'request'...st': 4.36, 'notes': 'Test Notes - Action Supply'}
        00:18:48.569227 call       624     def action_supply_credits_to_wallet(self, **kwargs):
        00:18:48.569360 line       625         log.debug('')
        00:18:48.569881 line       626         _credit_wallet = kwargs.get('credit_wallet') or \
        00:18:48.570061 line       627                 self.fetch_user_credit_wallet()
        New var:....... _credit_wallet = <base.credit_wallet.CreditEWallet object at 0xb6b8c04c>
        00:18:48.570611 line       628         if not _credit_wallet:
        00:18:48.570741 line       630         _supply = _credit_wallet.main_controller(
        00:18:48.571197 line       631                 controller='system', action='supply',
        00:18:48.571482 line       632                 credits=kwargs.get('credits') or 0
        New var:....... _supply = 0
        00:18:48.574482 line       634         return True if _supply else False
        00:18:48.574645 return     634         return True if _supply else False
        Return value:.. False
    New var:....... _supply_credits_to_remote = False
    00:18:48.574930 line       657         _local_transfer_sheet = _local_credit_wallet.fetch_credit_ewallet_transfer_sheet()
    New var:....... _local_transfer_sheet = <base.transfer_sheet.CreditTransferSheet object at 0xb6b1996c>
    00:18:48.589421 line       658         _local_invoice_sheet = _local_credit_wallet.fetch_credit_ewallet_invoice_sheet()
    New var:....... _local_invoice_sheet = <base.invoice_sheet.CreditInvoiceSheet object at 0xb6ad728c>
    00:18:48.601090 line       659         if not _local_transfer_sheet or not _local_invoice_sheet:
    00:18:48.601689 line       663         kwargs.pop('action')
    00:18:48.601912 line       664         _create_transfer_record = _local_transfer_sheet.credit_transfer_sheet_controller(
    00:18:48.602140 line       665                 action='add', transfer_type='outgoing', **kwargs,
    New var:....... _create_transfer_record = <base.transfer_sheet.CreditTransferSheetRecord object at 0xb6b7f40c>
    00:18:48.616313 line       667         _create_invoice_record = _local_invoice_sheet.credit_invoice_sheet_controller(
    00:18:48.616574 line       668                 action='add', seller_id=self.fetch_user_id(),
    00:18:48.617232 line       669                 transfer_record_id=_create_transfer_record.fetch_record_id(),
    00:18:48.617832 line       670                 **kwargs,
    New var:....... _create_invoice_record = <base.invoice_sheet.CreditInvoiceSheetRecord object at 0xb6b1fc8c>
    00:18:48.651580 line       673         _remote_transfer_sheet = _remote_credit_wallet.fetch_credit_ewallet_transfer_sheet()
    New var:....... _remote_transfer_sheet = <base.transfer_sheet.CreditTransferSheet object at 0xb6b1996c>
    00:18:48.653250 line       674         _remote_invoice_sheet = _remote_credit_wallet.fetch_credit_ewallet_invoice_sheet()
    New var:....... _remote_invoice_sheet = <base.invoice_sheet.CreditInvoiceSheet object at 0xb6ad728c>
    00:18:48.654068 line       676         if not _remote_transfer_sheet:
    00:18:48.654265 line       680         _share_transfer_record = _remote_transfer_sheet.credit_transfer_sheet_controller(
    00:18:48.654445 line       681                 action='add', transfer_type='incoming', **kwargs
    New var:....... _share_transfer_record = <base.transfer_sheet.CreditTransferSheetRecord object at 0xb6ad726c>
    00:18:48.658556 line       683         _share_invoice_record = _remote_invoice_sheet.credit_invoice_sheet_controller(
    00:18:48.659067 line       684                 action='add', seller_id=self.fetch_user_id(),
    00:18:48.660100 line       685                 transfer_record_id=_share_transfer_record.fetch_record_id(),
    00:18:48.660701 line       686                 **kwargs
    New var:....... _share_invoice_record = <base.invoice_sheet.CreditInvoiceSheetRecord object at 0xb6adc94c>
    00:18:48.663790 line       688         return True
    00:18:48.663989 return     688         return True
    Return value:.. True
    Starting var:.. self = <base.res_user.ResUser object at 0xb6bc616c>
    Starting var:.. kwargs = {'ctype': 'event', 'event': 'request', 'request'...st': 4.36, 'notes': 'Test Notes - Action Supply'}
    00:19:18.478656 call       638     def handle_user_event_request_credits(self, **kwargs):
    00:19:18.479737 line       639         log.debug('')
    00:19:18.480298 line       640         if not kwargs.get('partner_account'):
    00:19:18.480446 line       644         _local_credit_wallet = self.fetch_user_credit_wallet()
    New var:....... _local_credit_wallet = <base.credit_wallet.CreditEWallet object at 0xb6b9d62c>
    00:19:18.484105 line       645         _remote_credit_wallet = kwargs['partner_account'].fetch_user_credit_wallet()
    New var:....... _remote_credit_wallet = <base.credit_wallet.CreditEWallet object at 0xb6b9d62c>
    00:19:18.484891 line       647         if not _remote_credit_wallet:
    00:19:18.485315 line       654         _extract_credits_from_local = self.action_extract_credits_from_wallet(**kwargs)
        Starting var:.. self = <base.res_user.ResUser object at 0xb6bc616c>
        Starting var:.. kwargs = {'ctype': 'event', 'event': 'request', 'request'...st': 4.36, 'notes': 'Test Notes - Action Supply'}
        00:19:18.485668 call       611     def action_extract_credits_from_wallet(self, **kwargs):
        00:19:18.485833 line       612         log.debug('')
        00:19:18.486496 line       613         _credit_wallet = kwargs.get('credit_wallet') or \
        00:19:18.486723 line       614                 self.fetch_user_credit_wallet()
        New var:....... _credit_wallet = <base.credit_wallet.CreditEWallet object at 0xb6b9d62c>
        00:19:18.487469 line       615         if not _credit_wallet:
        00:19:18.487623 line       617         _extract = _credit_wallet.main_controller(
        00:19:18.487749 line       618                 controller='system', action='extract',
        00:19:18.487868 line       619                 credits=kwargs.get('credits') or 0
        New var:....... _extract = -10
        00:19:18.495659 line       621         return True if _extract else False
        00:19:18.495989 return     621         return True if _extract else False
        Return value:.. True
    New var:....... _extract_credits_from_local = True
    00:19:18.496290 line       655         _supply_credits_to_remote = kwargs['partner_account'].action_supply_credits_to_wallet(**kwargs)
        Starting var:.. self = <base.res_user.ResUser object at 0xb6bc616c>
        Starting var:.. kwargs = {'ctype': 'event', 'event': 'request', 'request'...st': 4.36, 'notes': 'Test Notes - Action Supply'}
        00:19:18.496551 call       624     def action_supply_credits_to_wallet(self, **kwargs):
        00:19:18.496678 line       625         log.debug('')
        00:19:18.500614 line       626         _credit_wallet = kwargs.get('credit_wallet') or \
        00:19:18.500910 line       627                 self.fetch_user_credit_wallet()
        New var:....... _credit_wallet = <base.credit_wallet.CreditEWallet object at 0xb6b9d62c>
        00:19:18.501664 line       628         if not _credit_wallet:
        00:19:18.501808 line       630         _supply = _credit_wallet.main_controller(
        00:19:18.501942 line       631                 controller='system', action='supply',
        00:19:18.504331 line       632                 credits=kwargs.get('credits') or 0
        New var:....... _supply = 0
        00:19:18.506651 line       634         return True if _supply else False
        00:19:18.506798 return     634         return True if _supply else False
        Return value:.. False
    New var:....... _supply_credits_to_remote = False
    00:19:18.507072 line       657         _local_transfer_sheet = _local_credit_wallet.fetch_credit_ewallet_transfer_sheet()
    New var:....... _local_transfer_sheet = <base.transfer_sheet.CreditTransferSheet object at 0xb6b4aa0c>
    00:19:18.528401 line       658         _local_invoice_sheet = _local_credit_wallet.fetch_credit_ewallet_invoice_sheet()
    New var:....... _local_invoice_sheet = <base.invoice_sheet.CreditInvoiceSheet object at 0xb6b8726c>
    00:19:18.536685 line       659         if not _local_transfer_sheet or not _local_invoice_sheet:
    00:19:18.536961 line       663         kwargs.pop('action')
    00:19:18.537243 line       664         _create_transfer_record = _local_transfer_sheet.credit_transfer_sheet_controller(
    00:19:18.537534 line       665                 action='add', transfer_type='outgoing', **kwargs,
    New var:....... _create_transfer_record = <base.transfer_sheet.CreditTransferSheetRecord object at 0xb6baa3cc>
    00:19:18.552963 line       667         _create_invoice_record = _local_invoice_sheet.credit_invoice_sheet_controller(
    00:19:18.553166 line       668                 action='add', seller_id=self.fetch_user_id(),
    00:19:18.553761 line       669                 transfer_record_id=_create_transfer_record.fetch_record_id(),
    00:19:18.554500 line       670                 **kwargs,
    New var:....... _create_invoice_record = <base.invoice_sheet.CreditInvoiceSheetRecord object at 0xb6b4ec6c>
    00:19:18.586043 line       673         _remote_transfer_sheet = _remote_credit_wallet.fetch_credit_ewallet_transfer_sheet()
    New var:....... _remote_transfer_sheet = <base.transfer_sheet.CreditTransferSheet object at 0xb6b4aa0c>
    00:19:18.587419 line       674         _remote_invoice_sheet = _remote_credit_wallet.fetch_credit_ewallet_invoice_sheet()
    New var:....... _remote_invoice_sheet = <base.invoice_sheet.CreditInvoiceSheet object at 0xb6b8726c>
    00:19:18.588076 line       676         if not _remote_transfer_sheet:
    00:19:18.588265 line       680         _share_transfer_record = _remote_transfer_sheet.credit_transfer_sheet_controller(
    00:19:18.588503 line       681                 action='add', transfer_type='incoming', **kwargs
    New var:....... _share_transfer_record = <base.transfer_sheet.CreditTransferSheetRecord object at 0xb6bbe6ac>
    00:19:18.592065 line       683         _share_invoice_record = _remote_invoice_sheet.credit_invoice_sheet_controller(
    00:19:18.592263 line       684                 action='add', seller_id=self.fetch_user_id(),
    00:19:18.592719 line       685                 transfer_record_id=_share_transfer_record.fetch_record_id(),
    00:19:18.593206 line       686                 **kwargs
    New var:....... _share_invoice_record = <base.invoice_sheet.CreditInvoiceSheetRecord object at 0xb6b0d9ec>
    00:19:18.595991 line       688         return True
    00:19:18.596188 return     688         return True
    Return value:.. True
Starting var:.. self = <__main__.EWallet object at 0xb6c5252c>
06:03:38.664544 call      2239     def test_view_credit_wallet(self):
06:03:38.665719 line      2240         print('[ * ] View Credit Wallet')
06:03:38.665855 line      2241         _view_credit_wallet = self.ewallet_controller(
06:03:38.665958 line      2242                 controller='user', ctype='action', action='view', view='credit_wallet',
06:03:38.683875 exception 2242                 controller='user', ctype='action', action='view', view='credit_wallet',
ValueError: Couldn't parse time string '1584158157.7077358' - value is not a string.
Call ended by exception
Starting var:.. self = <__main__.EWallet object at 0xb6cf974c>
06:06:12.768170 call      2239     def test_view_credit_wallet(self):
06:06:12.769242 line      2240         print('[ * ] View Credit Wallet')
06:06:12.769426 line      2241         _view_credit_wallet = self.ewallet_controller(
06:06:12.769548 line      2242                 controller='user', ctype='action', action='view', view='credit_wallet',
06:06:12.787510 exception 2242                 controller='user', ctype='action', action='view', view='credit_wallet',
ValueError: Couldn't parse datetime string '1584158157.7077358' - value is not a string.
Call ended by exception
Starting var:.. self = <__main__.EWallet object at 0xb6d84fcc>
06:07:07.215115 call      2239     def test_view_credit_wallet(self):
06:07:07.216194 line      2240         print('[ * ] View Credit Wallet')
06:07:07.216332 line      2241         _view_credit_wallet = self.ewallet_controller(
06:07:07.216436 line      2242                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b35a6c>]}
06:07:07.246396 line      2244         print(str(_view_credit_wallet) + '\n')
06:07:07.246612 line      2245         return _view_credit_wallet
06:07:07.246778 return    2245         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b35a6c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6db172c>
06:08:38.652997 call      2239     def test_view_credit_wallet(self):
06:08:38.654045 line      2240         print('[ * ] View Credit Wallet')
06:08:38.654203 line      2241         _view_credit_wallet = self.ewallet_controller(
06:08:38.654311 line      2242                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b62c4c>]}
06:08:38.686028 line      2244         print(str(_view_credit_wallet) + '\n')
06:08:38.686278 line      2245         return _view_credit_wallet
06:08:38.686427 return    2245         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b62c4c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6cedd8c>
06:09:39.330160 call      2239     def test_view_credit_wallet(self):
06:09:39.331269 line      2240         print('[ * ] View Credit Wallet')
06:09:39.331406 line      2241         _view_credit_wallet = self.ewallet_controller(
06:09:39.331507 line      2242                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b9222c>]}
06:09:39.358335 line      2244         print(str(_view_credit_wallet) + '\n')
06:09:39.358546 line      2245         return _view_credit_wallet
06:09:39.358695 return    2245         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b9222c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6c7f78c>
06:11:03.759833 call      2239     def test_view_credit_wallet(self):
06:11:03.761081 line      2240         print('[ * ] View Credit Wallet')
06:11:03.761216 line      2241         _view_credit_wallet = self.ewallet_controller(
06:11:03.761320 line      2242                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6aefd0c>]}
06:11:03.790712 line      2244         print(str(_view_credit_wallet) + '\n')
06:11:03.790920 line      2245         return _view_credit_wallet
06:11:03.791064 return    2245         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6aefd0c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6c80f4c>
06:32:41.397635 call      2239     def test_view_credit_wallet(self):
06:32:41.398846 line      2240         print('[ * ] View Credit Wallet')
06:32:41.399330 line      2241         _view_credit_wallet = self.ewallet_controller(
06:32:41.399995 line      2242                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6aa646c>]}
06:32:41.433145 line      2244         print(str(_view_credit_wallet) + '\n')
06:32:41.433387 line      2245         return _view_credit_wallet
06:32:41.433547 return    2245         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6aa646c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6c855ec>
06:32:47.954803 call      2239     def test_view_credit_wallet(self):
06:32:47.956064 line      2240         print('[ * ] View Credit Wallet')
06:32:47.956691 line      2241         _view_credit_wallet = self.ewallet_controller(
06:32:47.956999 line      2242                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b72e2c>]}
06:32:48.005985 line      2244         print(str(_view_credit_wallet) + '\n')
06:32:48.006858 line      2245         return _view_credit_wallet
06:32:48.007271 return    2245         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b72e2c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6d12e4c>
06:34:42.084992 call      2239     def test_view_credit_wallet(self):
06:34:42.086326 line      2240         print('[ * ] View Credit Wallet')
06:34:42.087069 line      2241         _view_credit_wallet = self.ewallet_controller(
06:34:42.087343 line      2242                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6a7956c>]}
06:34:42.123417 line      2244         print(str(_view_credit_wallet) + '\n')
06:34:42.124334 line      2245         return _view_credit_wallet
06:34:42.124640 return    2245         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6a7956c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6c578ec>
06:34:48.968445 call      2239     def test_view_credit_wallet(self):
06:34:48.969553 line      2240         print('[ * ] View Credit Wallet')
06:34:48.969701 line      2241         _view_credit_wallet = self.ewallet_controller(
06:34:48.969816 line      2242                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b44dcc>]}
06:34:49.003058 line      2244         print(str(_view_credit_wallet) + '\n')
06:34:49.003360 line      2245         return _view_credit_wallet
06:34:49.003526 return    2245         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b44dcc>]}
Starting var:.. self = <__main__.EWallet object at 0xb6cdff2c>
06:36:24.511780 call      2239     def test_view_credit_wallet(self):
06:36:24.513136 line      2240         print('[ * ] View Credit Wallet')
06:36:24.513284 line      2241         _view_credit_wallet = self.ewallet_controller(
06:36:24.513397 line      2242                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b064ec>]}
06:36:24.543635 line      2244         print(str(_view_credit_wallet) + '\n')
06:36:24.544731 line      2245         return _view_credit_wallet
06:36:24.545115 return    2245         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b064ec>]}
Starting var:.. self = <__main__.EWallet object at 0xb734b94c>
06:36:31.272341 call      2239     def test_view_credit_wallet(self):
06:36:31.273544 line      2240         print('[ * ] View Credit Wallet')
06:36:31.273748 line      2241         _view_credit_wallet = self.ewallet_controller(
06:36:31.273877 line      2242                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b78e2c>]}
06:36:31.310449 line      2244         print(str(_view_credit_wallet) + '\n')
06:36:31.310785 line      2245         return _view_credit_wallet
06:36:31.310980 return    2245         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b78e2c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6d92f2c>
16:23:54.465347 call      2239     def test_view_credit_wallet(self):
16:23:54.466913 line      2240         print('[ * ] View Credit Wallet')
16:23:54.467108 line      2241         _view_credit_wallet = self.ewallet_controller(
16:23:54.467233 line      2242                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6af85ec>]}
16:23:54.501731 line      2244         print(str(_view_credit_wallet) + '\n')
16:23:54.501977 line      2245         return _view_credit_wallet
16:23:54.502166 return    2245         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6af85ec>]}
Starting var:.. self = <__main__.EWallet object at 0xb6d659ac>
16:27:47.951514 call      2239     def test_view_credit_wallet(self):
16:27:47.953025 line      2240         print('[ * ] View Credit Wallet')
16:27:47.953236 line      2241         _view_credit_wallet = self.ewallet_controller(
16:27:47.953370 line      2242                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b14c6c>]}
16:27:47.993082 line      2244         print(str(_view_credit_wallet) + '\n')
16:27:47.993793 line      2245         return _view_credit_wallet
16:27:47.994090 return    2245         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b14c6c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6d0e98c>
16:37:46.657539 call      2239     def test_view_credit_wallet(self):
16:37:46.659335 line      2240         print('[ * ] View Credit Wallet')
16:37:46.659530 line      2241         _view_credit_wallet = self.ewallet_controller(
16:37:46.659670 line      2242                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6abcc2c>]}
16:37:46.697447 line      2244         print(str(_view_credit_wallet) + '\n')
16:37:46.697735 line      2245         return _view_credit_wallet
16:37:46.697938 return    2245         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6abcc2c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6da690c>
16:39:42.540669 call      2239     def test_view_credit_wallet(self):
16:39:42.542517 line      2240         print('[ * ] View Credit Wallet')
16:39:42.542701 line      2241         _view_credit_wallet = self.ewallet_controller(
16:39:42.542830 line      2242                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b59ccc>]}
16:39:42.584981 line      2244         print(str(_view_credit_wallet) + '\n')
16:39:42.585604 line      2245         return _view_credit_wallet
16:39:42.586035 return    2245         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b59ccc>]}
Starting var:.. self = <__main__.EWallet object at 0xb6d459ac>
16:40:19.826478 call      2239     def test_view_credit_wallet(self):
16:40:19.827909 line      2240         print('[ * ] View Credit Wallet')
16:40:19.828066 line      2241         _view_credit_wallet = self.ewallet_controller(
16:40:19.828178 line      2242                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6af3c8c>]}
16:40:19.870742 line      2244         print(str(_view_credit_wallet) + '\n')
16:40:19.871019 line      2245         return _view_credit_wallet
16:40:19.871199 return    2245         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6af3c8c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6d5d92c>
16:41:46.603741 call      2239     def test_view_credit_wallet(self):
16:41:46.605165 line      2240         print('[ * ] View Credit Wallet')
16:41:46.605360 line      2241         _view_credit_wallet = self.ewallet_controller(
16:41:46.605487 line      2242                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b0ac0c>]}
16:41:46.640002 line      2244         print(str(_view_credit_wallet) + '\n')
16:41:46.640317 line      2245         return _view_credit_wallet
16:41:46.640546 return    2245         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b0ac0c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6d3798c>
16:43:06.478932 call      2239     def test_view_credit_wallet(self):
16:43:06.480166 line      2240         print('[ * ] View Credit Wallet')
16:43:06.480359 line      2241         _view_credit_wallet = self.ewallet_controller(
16:43:06.480487 line      2242                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6ae4bec>]}
16:43:06.519713 line      2244         print(str(_view_credit_wallet) + '\n')
16:43:06.520052 line      2245         return _view_credit_wallet
16:43:06.520467 return    2245         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6ae4bec>]}
Starting var:.. self = <__main__.EWallet object at 0xb6d87bac>
16:44:52.420975 call      2239     def test_view_credit_wallet(self):
16:44:52.422186 line      2240         print('[ * ] View Credit Wallet')
16:44:52.422344 line      2241         _view_credit_wallet = self.ewallet_controller(
16:44:52.422460 line      2242                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b39c4c>]}
16:44:52.463209 line      2244         print(str(_view_credit_wallet) + '\n')
16:44:52.463440 line      2245         return _view_credit_wallet
16:44:52.463599 return    2245         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b39c4c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6dca96c>
16:48:06.882872 call      2239     def test_view_credit_wallet(self):
16:48:06.884007 line      2240         print('[ * ] View Credit Wallet')
16:48:06.884158 line      2241         _view_credit_wallet = self.ewallet_controller(
16:48:06.884278 line      2242                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b7fd6c>]}
16:48:06.920580 line      2244         print(str(_view_credit_wallet) + '\n')
16:48:06.920850 line      2245         return _view_credit_wallet
16:48:06.921032 return    2245         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b7fd6c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6d92aac>
16:49:53.120620 call      2239     def test_view_credit_wallet(self):
16:49:53.122267 line      2240         print('[ * ] View Credit Wallet')
16:49:53.122600 line      2241         _view_credit_wallet = self.ewallet_controller(
16:49:53.122751 line      2242                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b465cc>]}
16:49:53.162231 line      2244         print(str(_view_credit_wallet) + '\n')
16:49:53.162522 line      2245         return _view_credit_wallet
16:49:53.162725 return    2245         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b465cc>]}
Starting var:.. self = <__main__.EWallet object at 0xb6d45a2c>
16:51:28.923295 call      2239     def test_view_credit_wallet(self):
16:51:28.924590 line      2240         print('[ * ] View Credit Wallet')
16:51:28.924730 line      2241         _view_credit_wallet = self.ewallet_controller(
16:51:28.924952 line      2242                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6afa02c>]}
16:51:28.961267 line      2244         print(str(_view_credit_wallet) + '\n')
16:51:28.961517 line      2245         return _view_credit_wallet
16:51:28.961675 return    2245         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6afa02c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6d20a2c>
16:52:35.668240 call      2239     def test_view_credit_wallet(self):
16:52:35.669571 line      2240         print('[ * ] View Credit Wallet')
16:52:35.669788 line      2241         _view_credit_wallet = self.ewallet_controller(
16:52:35.669935 line      2242                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6ad2e2c>]}
16:52:35.709406 line      2244         print(str(_view_credit_wallet) + '\n')
16:52:35.709655 line      2245         return _view_credit_wallet
16:52:35.709810 return    2245         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6ad2e2c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6d07aac>
16:55:16.220309 call      2239     def test_view_credit_wallet(self):
16:55:16.221454 line      2240         print('[ * ] View Credit Wallet')
16:55:16.221601 line      2241         _view_credit_wallet = self.ewallet_controller(
16:55:16.221719 line      2242                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6aba0ec>]}
16:55:16.258648 line      2244         print(str(_view_credit_wallet) + '\n')
16:55:16.258945 line      2245         return _view_credit_wallet
16:55:16.259225 return    2245         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6aba0ec>]}
Starting var:.. self = <__main__.EWallet object at 0xb6d49a6c>
16:56:58.084297 call      2239     def test_view_credit_wallet(self):
16:56:58.085657 line      2240         print('[ * ] View Credit Wallet')
16:56:58.085963 line      2241         _view_credit_wallet = self.ewallet_controller(
16:56:58.086302 line      2242                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6afe0ac>]}
16:56:58.135197 line      2244         print(str(_view_credit_wallet) + '\n')
16:56:58.135599 line      2245         return _view_credit_wallet
16:56:58.135792 return    2245         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6afe0ac>]}
Starting var:.. self = <__main__.EWallet object at 0xb6db5a6c>
16:57:13.993444 call      2239     def test_view_credit_wallet(self):
16:57:13.995312 line      2240         print('[ * ] View Credit Wallet')
16:57:13.996033 line      2241         _view_credit_wallet = self.ewallet_controller(
16:57:13.996832 line      2242                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b6802c>]}
16:57:14.072588 line      2244         print(str(_view_credit_wallet) + '\n')
16:57:14.073377 line      2245         return _view_credit_wallet
16:57:14.085223 return    2245         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b6802c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6cf6e6c>
16:58:44.114747 call      2239     def test_view_credit_wallet(self):
16:58:44.116412 line      2240         print('[ * ] View Credit Wallet')
16:58:44.116762 line      2241         _view_credit_wallet = self.ewallet_controller(
16:58:44.116919 line      2242                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6aaa06c>]}
16:58:44.152297 line      2244         print(str(_view_credit_wallet) + '\n')
16:58:44.152602 line      2245         return _view_credit_wallet
16:58:44.152875 return    2245         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6aaa06c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6d32a8c>
17:03:56.903536 call      2239     def test_view_credit_wallet(self):
17:03:56.904841 line      2240         print('[ * ] View Credit Wallet')
17:03:56.905042 line      2241         _view_credit_wallet = self.ewallet_controller(
17:03:56.905178 line      2242                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6ae50ec>]}
17:03:56.945737 line      2244         print(str(_view_credit_wallet) + '\n')
17:03:56.945963 line      2245         return _view_credit_wallet
17:03:56.946140 return    2245         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6ae50ec>]}
Starting var:.. self = <__main__.EWallet object at 0xb6cdcaac>
17:04:37.973298 call      2239     def test_view_credit_wallet(self):
17:04:37.977287 line      2240         print('[ * ] View Credit Wallet')
17:04:37.977971 line      2241         _view_credit_wallet = self.ewallet_controller(
17:04:37.978297 line      2242                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6a905ac>]}
17:04:38.025624 line      2244         print(str(_view_credit_wallet) + '\n')
17:04:38.025871 line      2245         return _view_credit_wallet
17:04:38.026037 return    2245         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6a905ac>]}
Starting var:.. self = <__main__.EWallet object at 0xb6d01a4c>
17:04:59.329564 call      2239     def test_view_credit_wallet(self):
17:04:59.331266 line      2240         print('[ * ] View Credit Wallet')
17:04:59.331421 line      2241         _view_credit_wallet = self.ewallet_controller(
17:04:59.331536 line      2242                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6af55ac>]}
17:04:59.375616 line      2244         print(str(_view_credit_wallet) + '\n')
17:04:59.375978 line      2245         return _view_credit_wallet
17:04:59.376202 return    2245         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6af55ac>]}
Starting var:.. self = <__main__.EWallet object at 0xb6d6fb2c>
17:09:54.047460 call      2239     def test_view_credit_wallet(self):
17:09:54.048949 line      2240         print('[ * ] View Credit Wallet')
17:09:54.049110 line      2241         _view_credit_wallet = self.ewallet_controller(
17:09:54.049227 line      2242                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b2704c>]}
17:09:54.097095 line      2244         print(str(_view_credit_wallet) + '\n')
17:09:54.097464 line      2245         return _view_credit_wallet
17:09:54.097668 return    2245         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b2704c>]}
Starting var:.. self = <base.credit_clock.CreditClock object at 0xb6b2282c>
Starting var:.. args = ('time_start', 'time_stop')
17:09:57.536277 call       763     def clear_credit_clock_values(self, *args):
17:09:57.536540 line       764         log.debug('')
17:09:57.537273 line       766                 'wallet_id': self.set_credit_clock_wallet_id,
17:09:57.537505 line       767                 'reference': self.set_credit_clock_reference,
17:09:57.537644 line       768                 'create_date': self.set_credit_clock_create_date,
17:09:57.537753 line       769                 'write_date': self.set_credit_clock_write_date,
17:09:57.537856 line       770                 'credit_clock': self.set_credit_clock,
17:09:57.537957 line       771                 'credit_clock_state': self.set_credit_clock_state,
17:09:57.538314 line       772                 'time_spent': self.set_credit_clock_time_spent,
17:09:57.538594 line       773                 'time_start': self.set_credit_clock_time_start,
17:09:57.538754 line       774                 'time_stop': self.set_credit_clock_time_stop,
17:09:57.538954 line       775                 'wallet': self.set_credit_clock_wallet,
17:09:57.539415 line       776                 'time_sheet': self.set_credit_clock_time_sheet,
17:09:57.539535 line       777                 'active_time_record': self.set_credit_clock_active_time_record,
17:09:57.539640 line       778                 'conversion_sheet': self.set_credit_clock_conversion_sheet,
17:09:57.539754 line       779                 'time_sheet_archive': self.set_credit_clock_time_sheet_archive,
17:09:57.539873 line       780                 'conversion_sheet_archive': self.set_credit_clock_conversion_sheet_archive,
New var:....... _handlers = {'wallet_id': <bound method CreditClock.set_cred....credit_clock.CreditClock object at 0xb6b2282c>>}
17:09:57.540128 line       782         _clear_value_map = self.fetch_credit_clock_clear_value_map()
New var:....... _clear_value_map = {'wallet_id': None, 'reference': '', 'create_dat...eet_archive': [], 'conversion_sheet_archive': []}
17:09:57.540406 line       783         for item in args:
New var:....... item = 'time_start'
17:09:57.540656 line       784             if item not in _handlers:
17:09:57.540849 line       786             try:
17:09:57.541064 line       787                 _handlers[item](**{item: _clear_value_map[item]})
17:09:57.541296 exception  787                 _handlers[item](**{item: _clear_value_map[item]})
KeyError: 'time_start'
17:09:57.542082 line       788             except KeyError:
17:09:57.542662 line       789                 self.warning_could_not_clear_credit_clock_field()
17:09:57.543400 line       783         for item in args:
Modified var:.. item = 'time_stop'
17:09:57.543920 line       784             if item not in _handlers:
17:09:57.544413 line       786             try:
17:09:57.545240 line       787                 _handlers[item](**{item: _clear_value_map[item]})
17:09:57.545538 exception  787                 _handlers[item](**{item: _clear_value_map[item]})
KeyError: 'time_stop'
17:09:57.545951 line       788             except KeyError:
17:09:57.546457 line       789                 self.warning_could_not_clear_credit_clock_field()
17:09:57.547149 line       783         for item in args:
17:09:57.547346 line       790         return True
17:09:57.547511 return     790         return True
Return value:.. True
Starting var:.. self = <base.credit_clock.CreditClock object at 0xb6b2282c>
Starting var:.. args = ('start_time', 'end_time')
17:09:57.560363 call       763     def clear_credit_clock_values(self, *args):
17:09:57.560566 line       764         log.debug('')
17:09:57.561370 line       766                 'wallet_id': self.set_credit_clock_wallet_id,
17:09:57.561601 line       767                 'reference': self.set_credit_clock_reference,
17:09:57.561714 line       768                 'create_date': self.set_credit_clock_create_date,
17:09:57.561821 line       769                 'write_date': self.set_credit_clock_write_date,
17:09:57.561959 line       770                 'credit_clock': self.set_credit_clock,
17:09:57.562063 line       771                 'credit_clock_state': self.set_credit_clock_state,
17:09:57.562228 line       772                 'time_spent': self.set_credit_clock_time_spent,
17:09:57.562333 line       773                 'time_start': self.set_credit_clock_time_start,
17:09:57.562437 line       774                 'time_stop': self.set_credit_clock_time_stop,
17:09:57.562539 line       775                 'wallet': self.set_credit_clock_wallet,
17:09:57.562639 line       776                 'time_sheet': self.set_credit_clock_time_sheet,
17:09:57.562739 line       777                 'active_time_record': self.set_credit_clock_active_time_record,
17:09:57.562839 line       778                 'conversion_sheet': self.set_credit_clock_conversion_sheet,
17:09:57.562940 line       779                 'time_sheet_archive': self.set_credit_clock_time_sheet_archive,
17:09:57.563041 line       780                 'conversion_sheet_archive': self.set_credit_clock_conversion_sheet_archive,
New var:....... _handlers = {'wallet_id': <bound method CreditClock.set_cred....credit_clock.CreditClock object at 0xb6b2282c>>}
17:09:57.563285 line       782         _clear_value_map = self.fetch_credit_clock_clear_value_map()
New var:....... _clear_value_map = {'wallet_id': None, 'reference': '', 'create_dat...eet_archive': [], 'conversion_sheet_archive': []}
17:09:57.563530 line       783         for item in args:
New var:....... item = 'start_time'
17:09:57.563752 line       784             if item not in _handlers:
17:09:57.563915 line       785                 return self.error_invalid_field_for_credit_clock()
17:09:57.564514 return     785                 return self.error_invalid_field_for_credit_clock()
Return value:.. False
Starting var:.. self = <__main__.EWallet object at 0xb6d3daec>
17:11:28.229238 call      2239     def test_view_credit_wallet(self):
17:11:28.230941 line      2240         print('[ * ] View Credit Wallet')
17:11:28.231565 line      2241         _view_credit_wallet = self.ewallet_controller(
17:11:28.231780 line      2242                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6aef14c>]}
17:11:28.287632 line      2244         print(str(_view_credit_wallet) + '\n')
17:11:28.288829 line      2245         return _view_credit_wallet
17:11:28.289097 return    2245         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6aef14c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6cf2b4c>
17:13:16.831139 call      2239     def test_view_credit_wallet(self):
17:13:16.833149 line      2240         print('[ * ] View Credit Wallet')
17:13:16.833343 line      2241         _view_credit_wallet = self.ewallet_controller(
17:13:16.833464 line      2242                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6aaa04c>]}
17:13:16.877138 line      2244         print(str(_view_credit_wallet) + '\n')
17:13:16.877566 line      2245         return _view_credit_wallet
17:13:16.877782 return    2245         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6aaa04c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6d11b4c>
17:14:15.059469 call      2239     def test_view_credit_wallet(self):
17:14:15.061751 line      2240         print('[ * ] View Credit Wallet')
17:14:15.061906 line      2241         _view_credit_wallet = self.ewallet_controller(
17:14:15.062016 line      2242                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6acb04c>]}
17:14:15.116816 line      2244         print(str(_view_credit_wallet) + '\n')
17:14:15.117070 line      2245         return _view_credit_wallet
17:14:15.117228 return    2245         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6acb04c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6d98a8c>
17:16:05.656550 call      2239     def test_view_credit_wallet(self):
17:16:05.659331 line      2240         print('[ * ] View Credit Wallet')
17:16:05.659724 line      2241         _view_credit_wallet = self.ewallet_controller(
17:16:05.659890 line      2242                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b4c0ec>]}
17:16:05.696823 line      2244         print(str(_view_credit_wallet) + '\n')
17:16:05.697058 line      2245         return _view_credit_wallet
17:16:05.697212 return    2245         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b4c0ec>]}
Starting var:.. self = <__main__.EWallet object at 0xb6ce4aec>
17:19:27.812585 call      2239     def test_view_credit_wallet(self):
17:19:27.814018 line      2240         print('[ * ] View Credit Wallet')
17:19:27.814248 line      2241         _view_credit_wallet = self.ewallet_controller(
17:19:27.814388 line      2242                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6a9710c>]}
17:19:27.851281 line      2244         print(str(_view_credit_wallet) + '\n')
17:19:27.851523 line      2245         return _view_credit_wallet
17:19:27.851701 return    2245         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6a9710c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6d38aac>
17:22:57.001562 call      2239     def test_view_credit_wallet(self):
17:22:57.002918 line      2240         print('[ * ] View Credit Wallet')
17:22:57.003066 line      2241         _view_credit_wallet = self.ewallet_controller(
17:22:57.003180 line      2242                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6aeb10c>]}
17:22:57.036489 line      2244         print(str(_view_credit_wallet) + '\n')
17:22:57.036707 line      2245         return _view_credit_wallet
17:22:57.036863 return    2245         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6aeb10c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6d1ebec>
17:23:46.260970 call      2239     def test_view_credit_wallet(self):
17:23:46.262299 line      2240         print('[ * ] View Credit Wallet')
17:23:46.262519 line      2241         _view_credit_wallet = self.ewallet_controller(
17:23:46.262666 line      2242                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6ad20ec>]}
17:23:46.310224 line      2244         print(str(_view_credit_wallet) + '\n')
17:23:46.311364 line      2245         return _view_credit_wallet
17:23:46.311669 return    2245         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6ad20ec>]}
Starting var:.. self = <__main__.EWallet object at 0xb6d07aec>
17:24:41.008762 call      2239     def test_view_credit_wallet(self):
17:24:41.010956 line      2240         print('[ * ] View Credit Wallet')
17:24:41.011124 line      2241         _view_credit_wallet = self.ewallet_controller(
17:24:41.011234 line      2242                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6abb0cc>]}
17:24:41.052739 line      2244         print(str(_view_credit_wallet) + '\n')
17:24:41.052979 line      2245         return _view_credit_wallet
17:24:41.053126 return    2245         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6abb0cc>]}
Starting var:.. self = <__main__.EWallet object at 0xb6d75c0c>
17:33:47.573937 call      2239     def test_view_credit_wallet(self):
17:33:47.575133 line      2240         print('[ * ] View Credit Wallet')
17:33:47.575279 line      2241         _view_credit_wallet = self.ewallet_controller(
17:33:47.575401 line      2242                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b2d14c>]}
17:33:47.607386 line      2244         print(str(_view_credit_wallet) + '\n')
17:33:47.607603 line      2245         return _view_credit_wallet
17:33:47.607757 return    2245         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b2d14c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6daad6c>
17:37:30.584781 call      2239     def test_view_credit_wallet(self):
17:37:30.585953 line      2240         print('[ * ] View Credit Wallet')
17:37:30.586098 line      2241         _view_credit_wallet = self.ewallet_controller(
17:37:30.586240 line      2242                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b6218c>]}
17:37:30.635759 line      2244         print(str(_view_credit_wallet) + '\n')
17:37:30.636218 line      2245         return _view_credit_wallet
17:37:30.636460 return    2245         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b6218c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6dcebcc>
17:37:47.567521 call      2239     def test_view_credit_wallet(self):
17:37:47.569187 line      2240         print('[ * ] View Credit Wallet')
17:37:47.569392 line      2241         _view_credit_wallet = self.ewallet_controller(
17:37:47.569532 line      2242                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b8606c>]}
17:37:47.610935 line      2244         print(str(_view_credit_wallet) + '\n')
17:37:47.611169 line      2245         return _view_credit_wallet
17:37:47.611333 return    2245         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b8606c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6dadbcc>
17:40:58.886787 call      2239     def test_view_credit_wallet(self):
17:40:58.888056 line      2240         print('[ * ] View Credit Wallet')
17:40:58.888198 line      2241         _view_credit_wallet = self.ewallet_controller(
17:40:58.888312 line      2242                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b6616c>]}
17:40:58.921568 line      2244         print(str(_view_credit_wallet) + '\n')
17:40:58.921899 line      2245         return _view_credit_wallet
17:40:58.922095 return    2245         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b6616c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6d2ec0c>
17:41:53.679440 call      2239     def test_view_credit_wallet(self):
17:41:53.680551 line      2240         print('[ * ] View Credit Wallet')
17:41:53.680878 line      2241         _view_credit_wallet = self.ewallet_controller(
17:41:53.681022 line      2242                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6ae718c>]}
17:41:53.720302 line      2244         print(str(_view_credit_wallet) + '\n')
17:41:53.720642 line      2245         return _view_credit_wallet
17:41:53.720859 return    2245         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6ae718c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6dbdccc>
17:44:49.607348 call      2239     def test_view_credit_wallet(self):
17:44:49.608479 line      2240         print('[ * ] View Credit Wallet')
17:44:49.608625 line      2241         _view_credit_wallet = self.ewallet_controller(
17:44:49.608741 line      2242                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b7726c>]}
17:44:49.641724 line      2244         print(str(_view_credit_wallet) + '\n')
17:44:49.641969 line      2245         return _view_credit_wallet
17:44:49.642175 return    2245         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b7726c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6cecb4c>
17:48:58.194866 call      2239     def test_view_credit_wallet(self):
17:48:58.196258 line      2240         print('[ * ] View Credit Wallet')
17:48:58.196811 line      2241         _view_credit_wallet = self.ewallet_controller(
17:48:58.197080 line      2242                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6a9f14c>]}
17:48:58.278982 line      2244         print(str(_view_credit_wallet) + '\n')
17:48:58.279746 line      2245         return _view_credit_wallet
17:48:58.280030 return    2245         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6a9f14c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6cfec2c>
17:51:30.315341 call      2239     def test_view_credit_wallet(self):
17:51:30.316485 line      2240         print('[ * ] View Credit Wallet')
17:51:30.316634 line      2241         _view_credit_wallet = self.ewallet_controller(
17:51:30.316742 line      2242                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6ab70cc>]}
17:51:30.364844 line      2244         print(str(_view_credit_wallet) + '\n')
17:51:30.365518 line      2245         return _view_credit_wallet
17:51:30.365881 return    2245         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6ab70cc>]}
Starting var:.. self = <__main__.EWallet object at 0xb6d12bec>
17:58:29.585614 call      2239     def test_view_credit_wallet(self):
17:58:29.587045 line      2240         print('[ * ] View Credit Wallet')
17:58:29.587417 line      2241         _view_credit_wallet = self.ewallet_controller(
17:58:29.587608 line      2242                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6acc02c>]}
17:58:29.621879 line      2244         print(str(_view_credit_wallet) + '\n')
17:58:29.622095 line      2245         return _view_credit_wallet
17:58:29.622273 return    2245         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6acc02c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6c49d2c>
18:01:06.699752 call      2239     def test_view_credit_wallet(self):
18:01:06.700953 line      2240         print('[ * ] View Credit Wallet')
18:01:06.701101 line      2241         _view_credit_wallet = self.ewallet_controller(
18:01:06.701220 line      2242                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6ac10ac>]}
18:01:06.737590 line      2244         print(str(_view_credit_wallet) + '\n')
18:01:06.746308 line      2245         return _view_credit_wallet
18:01:06.746795 return    2245         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6ac10ac>]}
Starting var:.. self = <__main__.EWallet object at 0xb6c6bbcc>
18:06:25.910428 call      2239     def test_view_credit_wallet(self):
18:06:25.911708 line      2240         print('[ * ] View Credit Wallet')
18:06:25.911860 line      2241         _view_credit_wallet = self.ewallet_controller(
18:06:25.911974 line      2242                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b6506c>]}
18:06:25.951650 line      2244         print(str(_view_credit_wallet) + '\n')
18:06:25.951895 line      2245         return _view_credit_wallet
18:06:25.952044 return    2245         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b6506c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6cd6a2c>
18:27:52.219485 call      2239     def test_view_credit_wallet(self):
18:27:52.221319 line      2240         print('[ * ] View Credit Wallet')
18:27:52.221503 line      2241         _view_credit_wallet = self.ewallet_controller(
18:27:52.221620 line      2242                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b4b28c>]}
18:27:52.283269 line      2244         print(str(_view_credit_wallet) + '\n')
18:27:52.285212 line      2245         return _view_credit_wallet
18:27:52.285522 return    2245         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b4b28c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6d35dec>
19:12:50.243549 call      2232     def test_view_credit_wallet(self):
19:12:50.244678 line      2233         print('[ * ] View Credit Wallet')
19:12:50.244823 line      2234         _view_credit_wallet = self.ewallet_controller(
19:12:50.244939 line      2235                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6aed1ac>]}
19:12:50.282650 line      2237         print(str(_view_credit_wallet) + '\n')
19:12:50.283005 line      2238         return _view_credit_wallet
19:12:50.283191 return    2238         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6aed1ac>]}
Starting var:.. self = <__main__.EWallet object at 0xb73a50cc>
19:15:50.079207 call      2232     def test_view_credit_wallet(self):
19:15:50.080450 line      2233         print('[ * ] View Credit Wallet')
19:15:50.080728 line      2234         _view_credit_wallet = self.ewallet_controller(
19:15:50.084329 line      2235                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b8f76c>]}
19:15:50.123963 line      2237         print(str(_view_credit_wallet) + '\n')
19:15:50.124235 line      2238         return _view_credit_wallet
19:15:50.124402 return    2238         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b8f76c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6d08eec>
19:17:32.650893 call      2232     def test_view_credit_wallet(self):
19:17:32.653921 line      2233         print('[ * ] View Credit Wallet')
19:17:32.654236 line      2234         _view_credit_wallet = self.ewallet_controller(
19:17:32.654441 line      2235                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b8210c>]}
19:17:32.698820 line      2237         print(str(_view_credit_wallet) + '\n')
19:17:32.699779 line      2238         return _view_credit_wallet
19:17:32.700202 return    2238         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b8210c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6cd9eac>
19:19:18.586577 call      2232     def test_view_credit_wallet(self):
19:19:18.588105 line      2233         print('[ * ] View Credit Wallet')
19:19:18.588466 line      2234         _view_credit_wallet = self.ewallet_controller(
19:19:18.588614 line      2235                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b5224c>]}
19:19:18.636319 line      2237         print(str(_view_credit_wallet) + '\n')
19:19:18.636797 line      2238         return _view_credit_wallet
19:19:18.636974 return    2238         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b5224c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6cacdec>
19:19:45.061397 call      2232     def test_view_credit_wallet(self):
19:19:45.063187 line      2233         print('[ * ] View Credit Wallet')
19:19:45.064393 line      2234         _view_credit_wallet = self.ewallet_controller(
19:19:45.064755 line      2235                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6ada7cc>]}
19:19:45.099719 line      2237         print(str(_view_credit_wallet) + '\n')
19:19:45.099967 line      2238         return _view_credit_wallet
19:19:45.100147 return    2238         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6ada7cc>]}
Starting var:.. self = <__main__.EWallet object at 0xb6c5aeac>
19:23:18.565369 call      2231     def test_view_credit_wallet(self):
19:23:18.567473 line      2232         print('[ * ] View Credit Wallet')
19:23:18.568081 line      2233         _view_credit_wallet = self.ewallet_controller(
19:23:18.568349 line      2234                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6ad322c>]}
19:23:18.604686 line      2236         print(str(_view_credit_wallet) + '\n')
19:23:18.604939 line      2237         return _view_credit_wallet
19:23:18.605145 return    2237         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6ad322c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6c3aeac>
19:29:39.557969 call      2231     def test_view_credit_wallet(self):
19:29:39.560522 line      2232         print('[ * ] View Credit Wallet')
19:29:39.560704 line      2233         _view_credit_wallet = self.ewallet_controller(
19:29:39.560826 line      2234                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6ab23ac>]}
19:29:39.602520 line      2236         print(str(_view_credit_wallet) + '\n')
19:29:39.604121 line      2237         return _view_credit_wallet
19:29:39.604489 return    2237         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6ab23ac>]}
Starting var:.. self = <__main__.EWallet object at 0xb6cf850c>
19:30:39.883262 call      2231     def test_view_credit_wallet(self):
19:30:39.886737 line      2232         print('[ * ] View Credit Wallet')
19:30:39.886878 line      2233         _view_credit_wallet = self.ewallet_controller(
19:30:39.886987 line      2234                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b5d3ac>]}
19:30:39.943787 line      2236         print(str(_view_credit_wallet) + '\n')
19:30:39.944033 line      2237         return _view_credit_wallet
19:30:39.944623 return    2237         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b5d3ac>]}
Starting var:.. self = <__main__.EWallet object at 0xb6c10eec>
19:31:06.843135 call      2231     def test_view_credit_wallet(self):
19:31:06.844266 line      2232         print('[ * ] View Credit Wallet')
19:31:06.844415 line      2233         _view_credit_wallet = self.ewallet_controller(
19:31:06.844533 line      2234                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6a883cc>]}
19:31:06.880589 line      2236         print(str(_view_credit_wallet) + '\n')
19:31:06.880853 line      2237         return _view_credit_wallet
19:31:06.881062 return    2237         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6a883cc>]}
Starting var:.. self = <__main__.EWallet object at 0xb6c3ffcc>
19:31:44.590406 call      2231     def test_view_credit_wallet(self):
19:31:44.591584 line      2232         print('[ * ] View Credit Wallet')
19:31:44.591741 line      2233         _view_credit_wallet = self.ewallet_controller(
19:31:44.591857 line      2234                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6aba38c>]}
19:31:44.626578 line      2236         print(str(_view_credit_wallet) + '\n')
19:31:44.626874 line      2237         return _view_credit_wallet
19:31:44.627054 return    2237         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6aba38c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6c798ec>
19:32:45.452160 call      2231     def test_view_credit_wallet(self):
19:32:45.453330 line      2232         print('[ * ] View Credit Wallet')
19:32:45.453487 line      2233         _view_credit_wallet = self.ewallet_controller(
19:32:45.453605 line      2234                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6ae042c>]}
19:32:45.488982 line      2236         print(str(_view_credit_wallet) + '\n')
19:32:45.489362 line      2237         return _view_credit_wallet
19:32:45.489623 return    2237         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6ae042c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6c268ec>
19:33:56.076710 call      2231     def test_view_credit_wallet(self):
19:33:56.078070 line      2232         print('[ * ] View Credit Wallet')
19:33:56.078260 line      2233         _view_credit_wallet = self.ewallet_controller(
19:33:56.078375 line      2234                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6a8d20c>]}
19:33:56.116609 line      2236         print(str(_view_credit_wallet) + '\n')
19:33:56.116904 line      2237         return _view_credit_wallet
19:33:56.117471 return    2237         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6a8d20c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6c2b60c>
19:38:11.796829 call      2231     def test_view_credit_wallet(self):
19:38:11.797987 line      2232         print('[ * ] View Credit Wallet')
19:38:11.798179 line      2233         _view_credit_wallet = self.ewallet_controller(
19:38:11.798306 line      2234                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6a933ec>]}
19:38:11.837948 line      2236         print(str(_view_credit_wallet) + '\n')
19:38:11.838288 line      2237         return _view_credit_wallet
19:38:11.838470 return    2237         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6a933ec>]}
Starting var:.. self = <__main__.EWallet object at 0xb6ca3dec>
19:40:53.717835 call      2232     def test_view_credit_wallet(self):
19:40:53.718996 line      2233         print('[ * ] View Credit Wallet')
19:40:53.719143 line      2234         _view_credit_wallet = self.ewallet_controller(
19:40:53.719259 line      2235                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b1b2ec>]}
19:40:53.758787 line      2237         print(str(_view_credit_wallet) + '\n')
19:40:53.759166 line      2238         return _view_credit_wallet
19:40:53.759382 return    2238         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b1b2ec>]}
Starting var:.. self = <__main__.EWallet object at 0xb6cb42ac>
19:43:19.121593 call      2232     def test_view_credit_wallet(self):
19:43:19.123087 line      2233         print('[ * ] View Credit Wallet')
19:43:19.123282 line      2234         _view_credit_wallet = self.ewallet_controller(
19:43:19.123419 line      2235                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b182ac>]}
19:43:19.159182 line      2237         print(str(_view_credit_wallet) + '\n')
19:43:19.159428 line      2238         return _view_credit_wallet
19:43:19.159613 return    2238         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b182ac>]}
Starting var:.. self = <__main__.EWallet object at 0xb6d07fac>
19:46:01.530848 call      2232     def test_view_credit_wallet(self):
19:46:01.535379 line      2233         print('[ * ] View Credit Wallet')
19:46:01.535580 line      2234         _view_credit_wallet = self.ewallet_controller(
19:46:01.535684 line      2235                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b8056c>]}
19:46:01.578067 line      2237         print(str(_view_credit_wallet) + '\n')
19:46:01.578352 line      2238         return _view_credit_wallet
19:46:01.578624 return    2238         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b8056c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6c2a96c>
19:48:22.548092 call      2232     def test_view_credit_wallet(self):
19:48:22.549523 line      2233         print('[ * ] View Credit Wallet')
19:48:22.549695 line      2234         _view_credit_wallet = self.ewallet_controller(
19:48:22.549813 line      2235                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6a8f2ec>]}
19:48:22.587887 line      2237         print(str(_view_credit_wallet) + '\n')
19:48:22.588233 line      2238         return _view_credit_wallet
19:48:22.588389 return    2238         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6a8f2ec>]}
Starting var:.. self = <__main__.EWallet object at 0xb6c78dcc>
19:50:51.538368 call      2232     def test_view_credit_wallet(self):
19:50:51.539931 line      2233         print('[ * ] View Credit Wallet')
19:50:51.540201 line      2234         _view_credit_wallet = self.ewallet_controller(
19:50:51.540327 line      2235                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6ade38c>]}
19:50:51.587255 line      2237         print(str(_view_credit_wallet) + '\n')
19:50:51.587744 line      2238         return _view_credit_wallet
19:50:51.587939 return    2238         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6ade38c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6d21dec>
19:53:15.586393 call      2233     def test_view_credit_wallet(self):
19:53:15.587711 line      2234         print('[ * ] View Credit Wallet')
19:53:15.587898 line      2235         _view_credit_wallet = self.ewallet_controller(
19:53:15.588884 line      2236                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b9730c>]}
19:53:15.630577 line      2238         print(str(_view_credit_wallet) + '\n')
19:53:15.630796 line      2239         return _view_credit_wallet
19:53:15.630952 return    2239         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b9730c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6c6a06c>
19:54:42.654295 call      2233     def test_view_credit_wallet(self):
19:54:42.656209 line      2234         print('[ * ] View Credit Wallet')
19:54:42.656354 line      2235         _view_credit_wallet = self.ewallet_controller(
19:54:42.656468 line      2236                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6ad140c>]}
19:54:42.692543 line      2238         print(str(_view_credit_wallet) + '\n')
19:54:42.692813 line      2239         return _view_credit_wallet
19:54:42.692991 return    2239         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6ad140c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6cd6dec>
19:56:44.921127 call      2233     def test_view_credit_wallet(self):
19:56:44.922395 line      2234         print('[ * ] View Credit Wallet')
19:56:44.922583 line      2235         _view_credit_wallet = self.ewallet_controller(
19:56:44.922702 line      2236                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b3e3cc>]}
19:56:44.974244 line      2238         print(str(_view_credit_wallet) + '\n')
19:56:44.974478 line      2239         return _view_credit_wallet
19:56:44.974633 return    2239         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b3e3cc>]}
Starting var:.. self = <__main__.EWallet object at 0xb6ccbdec>
19:57:30.660568 call      2233     def test_view_credit_wallet(self):
19:57:30.661687 line      2234         print('[ * ] View Credit Wallet')
19:57:30.661832 line      2235         _view_credit_wallet = self.ewallet_controller(
19:57:30.661946 line      2236                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b3238c>]}
19:57:30.706767 line      2238         print(str(_view_credit_wallet) + '\n')
19:57:30.707967 line      2239         return _view_credit_wallet
19:57:30.708433 return    2239         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b3238c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6c6f06c>
20:27:22.496565 call      2233     def test_view_credit_wallet(self):
20:27:22.499053 line      2234         print('[ * ] View Credit Wallet')
20:27:22.499409 line      2235         _view_credit_wallet = self.ewallet_controller(
20:27:22.499569 line      2236                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6ad842c>]}
20:27:22.529333 line      2238         print(str(_view_credit_wallet) + '\n')
20:27:22.529582 line      2239         return _view_credit_wallet
20:27:22.529731 return    2239         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6ad842c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6ce7d6c>
20:28:17.697101 call      2233     def test_view_credit_wallet(self):
20:28:17.698187 line      2234         print('[ * ] View Credit Wallet')
20:28:17.698327 line      2235         _view_credit_wallet = self.ewallet_controller(
20:28:17.698441 line      2236                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b512ec>]}
20:28:17.727293 line      2238         print(str(_view_credit_wallet) + '\n')
20:28:17.727506 line      2239         return _view_credit_wallet
20:28:17.727659 return    2239         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b512ec>]}
Starting var:.. self = <__main__.EWallet object at 0xb6c7206c>
20:28:55.773298 call      2233     def test_view_credit_wallet(self):
20:28:55.774383 line      2234         print('[ * ] View Credit Wallet')
20:28:55.774517 line      2235         _view_credit_wallet = self.ewallet_controller(
20:28:55.774624 line      2236                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6ada36c>]}
20:28:55.804024 line      2238         print(str(_view_credit_wallet) + '\n')
20:28:55.804246 line      2239         return _view_credit_wallet
20:28:55.804415 return    2239         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6ada36c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6c5e06c>
20:30:30.617784 call      2233     def test_view_credit_wallet(self):
20:30:30.618978 line      2234         print('[ * ] View Credit Wallet')
20:30:30.619110 line      2235         _view_credit_wallet = self.ewallet_controller(
20:30:30.619211 line      2236                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6ac542c>]}
20:30:30.647451 line      2238         print(str(_view_credit_wallet) + '\n')
20:30:30.647656 line      2239         return _view_credit_wallet
20:30:30.647797 return    2239         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6ac542c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6d0d08c>
20:34:23.695026 call      2233     def test_view_credit_wallet(self):
20:34:23.696298 line      2234         print('[ * ] View Credit Wallet')
20:34:23.696429 line      2235         _view_credit_wallet = self.ewallet_controller(
20:34:23.696535 line      2236                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b743ec>]}
20:34:23.725472 line      2238         print(str(_view_credit_wallet) + '\n')
20:34:23.725682 line      2239         return _view_credit_wallet
20:34:23.725914 return    2239         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b743ec>]}
Starting var:.. self = <__main__.EWallet object at 0xb6d4ee6c>
20:42:36.670268 call      2233     def test_view_credit_wallet(self):
20:42:36.671344 line      2234         print('[ * ] View Credit Wallet')
20:42:36.671486 line      2235         _view_credit_wallet = self.ewallet_controller(
20:42:36.671602 line      2236                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b7c94c>]}
20:42:36.703721 line      2238         print(str(_view_credit_wallet) + '\n')
20:42:36.703973 line      2239         return _view_credit_wallet
20:42:36.704148 return    2239         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b7c94c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6c56a2c>
21:03:45.220600 call      2245     def test_view_credit_wallet(self):
21:03:45.221850 line      2246         print('[ * ] View Credit Wallet')
21:03:45.222033 line      2247         _view_credit_wallet = self.ewallet_controller(
21:03:45.222569 line      2248                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6acd02c>]}
21:03:45.258926 line      2250         print(str(_view_credit_wallet) + '\n')
21:03:45.259170 line      2251         return _view_credit_wallet
21:03:45.259323 return    2251         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6acd02c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6c115ac>
21:04:38.827773 call      2247     def test_view_credit_wallet(self):
21:04:38.829124 line      2248         print('[ * ] View Credit Wallet')
21:04:38.829278 line      2249         _view_credit_wallet = self.ewallet_controller(
21:04:38.829385 line      2250                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6aebe8c>]}
21:04:38.859296 line      2252         print(str(_view_credit_wallet) + '\n')
21:04:38.859496 line      2253         return _view_credit_wallet
21:04:38.859632 return    2253         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6aebe8c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6cc71ec>
21:08:04.869553 call      2251     def test_view_credit_wallet(self):
21:08:04.871109 line      2252         print('[ * ] View Credit Wallet')
21:08:04.871244 line      2253         _view_credit_wallet = self.ewallet_controller(
21:08:04.871352 line      2254                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6ba204c>]}
21:08:04.901524 line      2256         print(str(_view_credit_wallet) + '\n')
21:08:04.901744 line      2257         return _view_credit_wallet
21:08:04.901896 return    2257         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6ba204c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6c5816c>
21:10:32.882639 call      2256     def test_view_credit_wallet(self):
21:10:32.883849 line      2257         print('[ * ] View Credit Wallet')
21:10:32.883988 line      2258         _view_credit_wallet = self.ewallet_controller(
21:10:32.884093 line      2259                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b330cc>]}
21:10:32.912891 line      2261         print(str(_view_credit_wallet) + '\n')
21:10:32.913156 line      2262         return _view_credit_wallet
21:10:32.913308 return    2262         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b330cc>]}
Starting var:.. self = <__main__.EWallet object at 0xb732a72c>
21:15:00.837200 call      2258     def test_view_credit_wallet(self):
21:15:00.838548 line      2259         print('[ * ] View Credit Wallet')
21:15:00.838740 line      2260         _view_credit_wallet = self.ewallet_controller(
21:15:00.838877 line      2261                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b4a98c>]}
21:15:00.866583 line      2263         print(str(_view_credit_wallet) + '\n')
21:15:00.866859 line      2264         return _view_credit_wallet
21:15:00.867049 return    2264         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b4a98c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6c750cc>
21:19:21.237107 call      2262     def test_view_credit_wallet(self):
21:19:21.238363 line      2263         print('[ * ] View Credit Wallet')
21:19:21.238498 line      2264         _view_credit_wallet = self.ewallet_controller(
21:19:21.238604 line      2265                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b8162c>]}
21:19:21.270948 line      2267         print(str(_view_credit_wallet) + '\n')
21:19:21.271159 line      2268         return _view_credit_wallet
21:19:21.271307 return    2268         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b8162c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6c9712c>
21:19:53.309076 call      2266     def test_view_credit_wallet(self):
21:19:53.310400 line      2267         print('[ * ] View Credit Wallet')
21:19:53.310539 line      2268         _view_credit_wallet = self.ewallet_controller(
21:19:53.310643 line      2269                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6baa7ac>]}
21:19:53.340577 line      2271         print(str(_view_credit_wallet) + '\n')
21:19:53.340789 line      2272         return _view_credit_wallet
21:19:53.340939 return    2272         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6baa7ac>]}
Starting var:.. self = <__main__.EWallet object at 0xb6cca94c>
21:42:02.765234 call      2332     def test_view_credit_wallet(self):
21:42:02.767513 line      2333         print('[ * ] View Credit Wallet')
21:42:02.767730 line      2334         _view_credit_wallet = self.ewallet_controller(
21:42:02.767884 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
21:42:02.791916 exception 2335                 controller='user', ctype='action', action='view', view='credit_wallet',
sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such column: credit_clock.pending_t...credit_clock.wallet_id]
[parameters: (2,)]
(Background on this error at: http://sqlalche.me/e/e3q8)
Call ended by exception
Starting var:.. self = <__main__.EWallet object at 0xb6c65a4c>
21:42:18.691314 call      2332     def test_view_credit_wallet(self):
21:42:18.692691 line      2333         print('[ * ] View Credit Wallet')
21:42:18.692938 line      2334         _view_credit_wallet = self.ewallet_controller(
21:42:18.693067 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b1b46c>]}
21:42:18.737197 line      2337         print(str(_view_credit_wallet) + '\n')
21:42:18.737992 line      2338         return _view_credit_wallet
21:42:18.738177 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b1b46c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6c90c2c>
21:44:23.719374 call      2332     def test_view_credit_wallet(self):
21:44:23.720807 line      2333         print('[ * ] View Credit Wallet')
21:44:23.721203 line      2334         _view_credit_wallet = self.ewallet_controller(
21:44:23.721494 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b0b64c>]}
21:44:23.758444 line      2337         print(str(_view_credit_wallet) + '\n')
21:44:23.758711 line      2338         return _view_credit_wallet
21:44:23.758978 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b0b64c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6ca8b0c>
21:50:17.663023 call      2332     def test_view_credit_wallet(self):
21:50:17.664170 line      2333         print('[ * ] View Credit Wallet')
21:50:17.664321 line      2334         _view_credit_wallet = self.ewallet_controller(
21:50:17.664442 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b2694c>]}
21:50:17.696326 line      2337         print(str(_view_credit_wallet) + '\n')
21:50:17.696588 line      2338         return _view_credit_wallet
21:50:17.696748 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b2694c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6cd7dac>
22:12:55.441863 call      2332     def test_view_credit_wallet(self):
22:12:55.443123 line      2333         print('[ * ] View Credit Wallet')
22:12:55.443270 line      2334         _view_credit_wallet = self.ewallet_controller(
22:12:55.443386 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6ad486c>]}
22:12:55.483714 line      2337         print(str(_view_credit_wallet) + '\n')
22:12:55.483966 line      2338         return _view_credit_wallet
22:12:55.484130 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6ad486c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6d53dac>
22:14:09.213381 call      2332     def test_view_credit_wallet(self):
22:14:09.216269 line      2333         print('[ * ] View Credit Wallet')
22:14:09.216454 line      2334         _view_credit_wallet = self.ewallet_controller(
22:14:09.216574 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b5280c>]}
22:14:09.257357 line      2337         print(str(_view_credit_wallet) + '\n')
22:14:09.257592 line      2338         return _view_credit_wallet
22:14:09.257754 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b5280c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6cc9bac>
22:14:26.511631 call      2332     def test_view_credit_wallet(self):
22:14:26.512991 line      2333         print('[ * ] View Credit Wallet')
22:14:26.513195 line      2334         _view_credit_wallet = self.ewallet_controller(
22:14:26.513334 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b855cc>]}
22:14:26.550093 line      2337         print(str(_view_credit_wallet) + '\n')
22:14:26.550347 line      2338         return _view_credit_wallet
22:14:26.550603 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b855cc>]}
Starting var:.. self = <__main__.EWallet object at 0xb6c38fcc>
22:14:47.627387 call      2332     def test_view_credit_wallet(self):
22:14:47.628596 line      2333         print('[ * ] View Credit Wallet')
22:14:47.628751 line      2334         _view_credit_wallet = self.ewallet_controller(
22:14:47.628872 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6ab68ec>]}
22:14:47.671244 line      2337         print(str(_view_credit_wallet) + '\n')
22:14:47.671519 line      2338         return _view_credit_wallet
22:14:47.671687 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6ab68ec>]}
Starting var:.. self = <__main__.EWallet object at 0xb6d66d6c>
22:15:19.810534 call      2332     def test_view_credit_wallet(self):
22:15:19.812078 line      2333         print('[ * ] View Credit Wallet')
22:15:19.812273 line      2334         _view_credit_wallet = self.ewallet_controller(
22:15:19.812541 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b6582c>]}
22:15:19.860357 line      2337         print(str(_view_credit_wallet) + '\n')
22:15:19.860698 line      2338         return _view_credit_wallet
22:15:19.860975 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b6582c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6ce1dac>
22:16:25.072913 call      2332     def test_view_credit_wallet(self):
22:16:25.074451 line      2333         print('[ * ] View Credit Wallet')
22:16:25.074609 line      2334         _view_credit_wallet = self.ewallet_controller(
22:16:25.074723 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6ae184c>]}
22:16:25.117380 line      2337         print(str(_view_credit_wallet) + '\n')
22:16:25.117615 line      2338         return _view_credit_wallet
22:16:25.117787 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6ae184c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6d63dcc>
22:16:57.311927 call      2332     def test_view_credit_wallet(self):
22:16:57.313203 line      2333         print('[ * ] View Credit Wallet')
22:16:57.313360 line      2334         _view_credit_wallet = self.ewallet_controller(
22:16:57.313476 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b248ec>]}
22:16:57.363593 line      2337         print(str(_view_credit_wallet) + '\n')
22:16:57.363854 line      2338         return _view_credit_wallet
22:16:57.364036 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b248ec>]}
Starting var:.. self = <__main__.EWallet object at 0xb6c9fb6c>
22:17:44.706926 call      2332     def test_view_credit_wallet(self):
22:17:44.708225 line      2333         print('[ * ] View Credit Wallet')
22:17:44.708381 line      2334         _view_credit_wallet = self.ewallet_controller(
22:17:44.708981 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b1d92c>]}
22:17:44.752044 line      2337         print(str(_view_credit_wallet) + '\n')
22:17:44.752279 line      2338         return _view_credit_wallet
22:17:44.752444 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b1d92c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6c18b4c>
22:19:37.555008 call      2332     def test_view_credit_wallet(self):
22:19:37.556263 line      2333         print('[ * ] View Credit Wallet')
22:19:37.556418 line      2334         _view_credit_wallet = self.ewallet_controller(
22:19:37.556536 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6a969ec>]}
22:19:37.603929 line      2337         print(str(_view_credit_wallet) + '\n')
22:19:37.604257 line      2338         return _view_credit_wallet
22:19:37.604444 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6a969ec>]}
Starting var:.. self = <__main__.EWallet object at 0xb6ca2b6c>
22:20:18.688373 call      2332     def test_view_credit_wallet(self):
22:20:18.689685 line      2333         print('[ * ] View Credit Wallet')
22:20:18.689842 line      2334         _view_credit_wallet = self.ewallet_controller(
22:20:18.689958 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b2090c>]}
22:20:18.730212 line      2337         print(str(_view_credit_wallet) + '\n')
22:20:18.730445 line      2338         return _view_credit_wallet
22:20:18.730601 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b2090c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6db5d4c>
22:22:21.908843 call      2332     def test_view_credit_wallet(self):
22:22:21.911209 line      2333         print('[ * ] View Credit Wallet')
22:22:21.911389 line      2334         _view_credit_wallet = self.ewallet_controller(
22:22:21.911512 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b7580c>]}
22:22:21.957180 line      2337         print(str(_view_credit_wallet) + '\n')
22:22:21.957434 line      2338         return _view_credit_wallet
22:22:21.957689 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b7580c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6d61dec>
22:23:08.061124 call      2332     def test_view_credit_wallet(self):
22:23:08.062434 line      2333         print('[ * ] View Credit Wallet')
22:23:08.062968 line      2334         _view_credit_wallet = self.ewallet_controller(
22:23:08.063181 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b5f92c>]}
22:23:08.108190 line      2337         print(str(_view_credit_wallet) + '\n')
22:23:08.108425 line      2338         return _view_credit_wallet
22:23:08.108586 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b5f92c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6d75d8c>
22:25:40.000943 call      2332     def test_view_credit_wallet(self):
22:25:40.003500 line      2333         print('[ * ] View Credit Wallet')
22:25:40.004082 line      2334         _view_credit_wallet = self.ewallet_controller(
22:25:40.004299 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b348ac>]}
22:25:40.054021 line      2337         print(str(_view_credit_wallet) + '\n')
22:25:40.054575 line      2338         return _view_credit_wallet
22:25:40.054765 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b348ac>]}
Starting var:.. self = <__main__.EWallet object at 0xb6daadec>
22:29:04.346382 call      2332     def test_view_credit_wallet(self):
22:29:04.347692 line      2333         print('[ * ] View Credit Wallet')
22:29:04.347847 line      2334         _view_credit_wallet = self.ewallet_controller(
22:29:04.347961 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b698ec>]}
22:29:04.401394 line      2337         print(str(_view_credit_wallet) + '\n')
22:29:04.401718 line      2338         return _view_credit_wallet
22:29:04.401958 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b698ec>]}
Starting var:.. self = <__main__.EWallet object at 0xb6d19dcc>
22:30:09.262059 call      2332     def test_view_credit_wallet(self):
22:30:09.263304 line      2333         print('[ * ] View Credit Wallet')
22:30:09.263458 line      2334         _view_credit_wallet = self.ewallet_controller(
22:30:09.263573 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b1788c>]}
22:30:09.301645 line      2337         print(str(_view_credit_wallet) + '\n')
22:30:09.301897 line      2338         return _view_credit_wallet
22:30:09.302053 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b1788c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6cb1c6c>
22:30:20.845538 call      2332     def test_view_credit_wallet(self):
22:30:20.846667 line      2333         print('[ * ] View Credit Wallet')
22:30:20.847402 line      2334         _view_credit_wallet = self.ewallet_controller(
22:30:20.847597 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b2ea8c>]}
22:30:20.887982 line      2337         print(str(_view_credit_wallet) + '\n')
22:30:20.888557 line      2338         return _view_credit_wallet
22:30:20.888759 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b2ea8c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6cd5bec>
22:31:55.143044 call      2332     def test_view_credit_wallet(self):
22:31:55.144980 line      2333         print('[ * ] View Credit Wallet')
22:31:55.145376 line      2334         _view_credit_wallet = self.ewallet_controller(
22:31:55.145518 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6bd1a2c>]}
22:31:55.189021 line      2337         print(str(_view_credit_wallet) + '\n')
22:31:55.189521 line      2338         return _view_credit_wallet
22:31:55.189744 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6bd1a2c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6c50c0c>
22:33:34.032626 call      2332     def test_view_credit_wallet(self):
22:33:34.034150 line      2333         print('[ * ] View Credit Wallet')
22:33:34.034933 line      2334         _view_credit_wallet = self.ewallet_controller(
22:33:34.035209 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b4ca2c>]}
22:33:34.083961 line      2337         print(str(_view_credit_wallet) + '\n')
22:33:34.084677 line      2338         return _view_credit_wallet
22:33:34.084919 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b4ca2c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6d14e0c>
22:35:49.886447 call      2332     def test_view_credit_wallet(self):
22:35:49.887706 line      2333         print('[ * ] View Credit Wallet')
22:35:49.887893 line      2334         _view_credit_wallet = self.ewallet_controller(
22:35:49.888022 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6ad48cc>]}
22:35:49.930963 line      2337         print(str(_view_credit_wallet) + '\n')
22:35:49.931206 line      2338         return _view_credit_wallet
22:35:49.931662 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6ad48cc>]}
Starting var:.. self = <__main__.EWallet object at 0xb6c26bcc>
22:36:29.930125 call      2332     def test_view_credit_wallet(self):
22:36:29.931349 line      2333         print('[ * ] View Credit Wallet')
22:36:29.931878 line      2334         _view_credit_wallet = self.ewallet_controller(
22:36:29.932127 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b239ec>]}
22:36:29.970758 line      2337         print(str(_view_credit_wallet) + '\n')
22:36:29.971014 line      2338         return _view_credit_wallet
22:36:29.971177 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b239ec>]}
Starting var:.. self = <__main__.EWallet object at 0xb6d2beac>
22:38:29.122602 call      2332     def test_view_credit_wallet(self):
22:38:29.124950 line      2333         print('[ * ] View Credit Wallet')
22:38:29.125461 line      2334         _view_credit_wallet = self.ewallet_controller(
22:38:29.125819 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b288cc>]}
22:38:29.167854 line      2337         print(str(_view_credit_wallet) + '\n')
22:38:29.168403 line      2338         return _view_credit_wallet
22:38:29.168596 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b288cc>]}
Starting var:.. self = <__main__.EWallet object at 0xb6cfaecc>
22:41:44.784444 call      2332     def test_view_credit_wallet(self):
22:41:44.785612 line      2333         print('[ * ] View Credit Wallet')
22:41:44.786162 line      2334         _view_credit_wallet = self.ewallet_controller(
22:41:44.787312 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6af78ec>]}
22:41:44.828976 line      2337         print(str(_view_credit_wallet) + '\n')
22:41:44.829316 line      2338         return _view_credit_wallet
22:41:44.829484 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6af78ec>]}
Starting var:.. self = <__main__.EWallet object at 0xb6d2feec>
22:43:56.850517 call      2332     def test_view_credit_wallet(self):
22:43:56.851996 line      2333         print('[ * ] View Credit Wallet')
22:43:56.852319 line      2334         _view_credit_wallet = self.ewallet_controller(
22:43:56.852464 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6aed8ac>]}
22:43:56.892818 line      2337         print(str(_view_credit_wallet) + '\n')
22:43:56.893079 line      2338         return _view_credit_wallet
22:43:56.893256 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6aed8ac>]}
Starting var:.. self = <__main__.EWallet object at 0xb6c62cac>
22:44:39.137996 call      2332     def test_view_credit_wallet(self):
22:44:39.139447 line      2333         print('[ * ] View Credit Wallet')
22:44:39.139891 line      2334         _view_credit_wallet = self.ewallet_controller(
22:44:39.140103 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b5f9ec>]}
22:44:39.186206 line      2337         print(str(_view_credit_wallet) + '\n')
22:44:39.186848 line      2338         return _view_credit_wallet
22:44:39.187112 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b5f9ec>]}
Starting var:.. self = <__main__.EWallet object at 0xb6d05f0c>
22:46:10.504905 call      2332     def test_view_credit_wallet(self):
22:46:10.509834 line      2333         print('[ * ] View Credit Wallet')
22:46:10.510082 line      2334         _view_credit_wallet = self.ewallet_controller(
22:46:10.510196 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6af194c>]}
22:46:10.586513 line      2337         print(str(_view_credit_wallet) + '\n')
22:46:10.586799 line      2338         return _view_credit_wallet
22:46:10.587241 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6af194c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6d68f6c>
22:46:52.774941 call      2332     def test_view_credit_wallet(self):
22:46:52.776995 line      2333         print('[ * ] View Credit Wallet')
22:46:52.777143 line      2334         _view_credit_wallet = self.ewallet_controller(
22:46:52.777258 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b5498c>]}
22:46:52.830267 line      2337         print(str(_view_credit_wallet) + '\n')
22:46:52.830485 line      2338         return _view_credit_wallet
22:46:52.830633 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b5498c>]}
Starting var:.. self = <__main__.EWallet object at 0xb7383fcc>
22:47:34.474846 call      2332     def test_view_credit_wallet(self):
22:47:34.476095 line      2333         print('[ * ] View Credit Wallet')
22:47:34.476245 line      2334         _view_credit_wallet = self.ewallet_controller(
22:47:34.476530 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b638ac>]}
22:47:34.529393 line      2337         print(str(_view_credit_wallet) + '\n')
22:47:34.529666 line      2338         return _view_credit_wallet
22:47:34.529840 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b638ac>]}
Starting var:.. self = <__main__.EWallet object at 0xb6cacd2c>
22:47:52.093861 call      2332     def test_view_credit_wallet(self):
22:47:52.095082 line      2333         print('[ * ] View Credit Wallet')
22:47:52.095384 line      2334         _view_credit_wallet = self.ewallet_controller(
22:47:52.095521 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6ba9a8c>]}
22:47:52.136494 line      2337         print(str(_view_credit_wallet) + '\n')
22:47:52.137260 line      2338         return _view_credit_wallet
22:47:52.137454 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6ba9a8c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6d54ecc>
22:52:30.985481 call      2332     def test_view_credit_wallet(self):
22:52:30.987008 line      2333         print('[ * ] View Credit Wallet')
22:52:30.987162 line      2334         _view_credit_wallet = self.ewallet_controller(
22:52:30.987276 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b0192c>]}
22:52:31.038523 line      2337         print(str(_view_credit_wallet) + '\n')
22:52:31.038799 line      2338         return _view_credit_wallet
22:52:31.039037 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b0192c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6cbe60c>
22:53:31.240924 call      2332     def test_view_credit_wallet(self):
22:53:31.242433 line      2333         print('[ * ] View Credit Wallet')
22:53:31.242583 line      2334         _view_credit_wallet = self.ewallet_controller(
22:53:31.242734 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b29a0c>]}
22:53:31.279254 line      2337         print(str(_view_credit_wallet) + '\n')
22:53:31.279542 line      2338         return _view_credit_wallet
22:53:31.279750 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b29a0c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6da97ec>
22:57:14.611201 call      2332     def test_view_credit_wallet(self):
22:57:14.612371 line      2333         print('[ * ] View Credit Wallet')
22:57:14.612676 line      2334         _view_credit_wallet = self.ewallet_controller(
22:57:14.612812 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b589ac>]}
22:57:14.665744 line      2337         print(str(_view_credit_wallet) + '\n')
22:57:14.666314 line      2338         return _view_credit_wallet
22:57:14.666529 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b589ac>]}
Starting var:.. self = <__main__.EWallet object at 0xb6cf7f0c>
22:58:58.042766 call      2332     def test_view_credit_wallet(self):
22:58:58.043995 line      2333         print('[ * ] View Credit Wallet')
22:58:58.044447 line      2334         _view_credit_wallet = self.ewallet_controller(
22:58:58.044672 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6ae49ec>]}
22:58:58.091494 line      2337         print(str(_view_credit_wallet) + '\n')
22:58:58.092149 line      2338         return _view_credit_wallet
22:58:58.092352 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6ae49ec>]}
Starting var:.. self = <__main__.EWallet object at 0xb6d4e5cc>
23:00:43.946015 call      2332     def test_view_credit_wallet(self):
23:00:43.947284 line      2333         print('[ * ] View Credit Wallet')
23:00:43.947432 line      2334         _view_credit_wallet = self.ewallet_controller(
23:00:43.947549 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6afd9ac>]}
23:00:43.985170 line      2337         print(str(_view_credit_wallet) + '\n')
23:00:43.985403 line      2338         return _view_credit_wallet
23:00:43.985559 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6afd9ac>]}
Starting var:.. self = <__main__.EWallet object at 0xb6d415ec>
23:14:44.890273 call      2332     def test_view_credit_wallet(self):
23:14:44.891415 line      2333         print('[ * ] View Credit Wallet')
23:14:44.891546 line      2334         _view_credit_wallet = self.ewallet_controller(
23:14:44.891650 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6aebb8c>]}
23:14:44.921727 line      2337         print(str(_view_credit_wallet) + '\n')
23:14:44.921940 line      2338         return _view_credit_wallet
23:14:44.922093 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6aebb8c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6c47e2c>
23:23:00.928201 call      2332     def test_view_credit_wallet(self):
23:23:00.929362 line      2333         print('[ * ] View Credit Wallet')
23:23:00.929507 line      2334         _view_credit_wallet = self.ewallet_controller(
23:23:00.929621 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b43cec>]}
23:23:00.968693 line      2337         print(str(_view_credit_wallet) + '\n')
23:23:00.969045 line      2338         return _view_credit_wallet
23:23:00.969318 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b43cec>]}
Starting var:.. self = <__main__.EWallet object at 0xb6c74e8c>
23:24:30.832475 call      2332     def test_view_credit_wallet(self):
23:24:30.833758 line      2333         print('[ * ] View Credit Wallet')
23:24:30.833913 line      2334         _view_credit_wallet = self.ewallet_controller(
23:24:30.834027 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b70c0c>]}
23:24:30.871431 line      2337         print(str(_view_credit_wallet) + '\n')
23:24:30.871658 line      2338         return _view_credit_wallet
23:24:30.871810 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b70c0c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6dd906c>
23:25:10.993396 call      2332     def test_view_credit_wallet(self):
23:25:10.996535 line      2333         print('[ * ] View Credit Wallet')
23:25:10.996710 line      2334         _view_credit_wallet = self.ewallet_controller(
23:25:10.996822 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b899ac>]}
23:25:11.041972 line      2337         print(str(_view_credit_wallet) + '\n')
23:25:11.042208 line      2338         return _view_credit_wallet
23:25:11.042362 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b899ac>]}
Starting var:.. self = <__main__.EWallet object at 0xb6d0c0ac>
23:25:59.642801 call      2332     def test_view_credit_wallet(self):
23:25:59.644845 line      2333         print('[ * ] View Credit Wallet')
23:25:59.645679 line      2334         _view_credit_wallet = self.ewallet_controller(
23:25:59.645948 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6abb9ec>]}
23:25:59.700794 line      2337         print(str(_view_credit_wallet) + '\n')
23:25:59.703117 line      2338         return _view_credit_wallet
23:25:59.703430 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6abb9ec>]}
Starting var:.. self = <__main__.EWallet object at 0xb6d930ac>
23:27:12.999281 call      2332     def test_view_credit_wallet(self):
23:27:13.001494 line      2333         print('[ * ] View Credit Wallet')
23:27:13.001640 line      2334         _view_credit_wallet = self.ewallet_controller(
23:27:13.001755 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b85a0c>]}
23:27:13.045883 line      2337         print(str(_view_credit_wallet) + '\n')
23:27:13.046154 line      2338         return _view_credit_wallet
23:27:13.046346 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b85a0c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6c871ec>
23:31:39.837307 call      2332     def test_view_credit_wallet(self):
23:31:39.838898 line      2333         print('[ * ] View Credit Wallet')
23:31:39.839136 line      2334         _view_credit_wallet = self.ewallet_controller(
23:31:39.839271 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6af8b8c>]}
23:31:39.871320 line      2337         print(str(_view_credit_wallet) + '\n')
23:31:39.871607 line      2338         return _view_credit_wallet
23:31:39.871816 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6af8b8c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6ca772c>
23:32:17.034994 call      2332     def test_view_credit_wallet(self):
23:32:17.036097 line      2333         print('[ * ] View Credit Wallet')
23:32:17.036236 line      2334         _view_credit_wallet = self.ewallet_controller(
23:32:17.036345 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b18b6c>]}
23:32:17.069857 line      2337         print(str(_view_credit_wallet) + '\n')
23:32:17.070071 line      2338         return _view_credit_wallet
23:32:17.070215 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b18b6c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6cc318c>
23:34:17.407215 call      2332     def test_view_credit_wallet(self):
23:34:17.408330 line      2333         print('[ * ] View Credit Wallet')
23:34:17.408469 line      2334         _view_credit_wallet = self.ewallet_controller(
23:34:17.408576 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b34b6c>]}
23:34:17.442012 line      2337         print(str(_view_credit_wallet) + '\n')
23:34:17.442248 line      2338         return _view_credit_wallet
23:34:17.442402 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b34b6c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6c4d12c>
23:35:03.494959 call      2332     def test_view_credit_wallet(self):
23:35:03.496216 line      2333         print('[ * ] View Credit Wallet')
23:35:03.496346 line      2334         _view_credit_wallet = self.ewallet_controller(
23:35:03.496450 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6abdb0c>]}
23:35:03.527785 line      2337         print(str(_view_credit_wallet) + '\n')
23:35:03.528157 line      2338         return _view_credit_wallet
23:35:03.528351 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6abdb0c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6cb212c>
23:36:14.332206 call      2332     def test_view_credit_wallet(self):
23:36:14.333631 line      2333         print('[ * ] View Credit Wallet')
23:36:14.334114 line      2334         _view_credit_wallet = self.ewallet_controller(
23:36:14.334253 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b23b8c>]}
23:36:14.367390 line      2337         print(str(_view_credit_wallet) + '\n')
23:36:14.367601 line      2338         return _view_credit_wallet
23:36:14.367743 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b23b8c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6c9e16c>
23:37:12.388951 call      2332     def test_view_credit_wallet(self):
23:37:12.390116 line      2333         print('[ * ] View Credit Wallet')
23:37:12.390252 line      2334         _view_credit_wallet = self.ewallet_controller(
23:37:12.390360 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b10b6c>]}
23:37:12.422915 line      2337         print(str(_view_credit_wallet) + '\n')
23:37:12.423124 line      2338         return _view_credit_wallet
23:37:12.423268 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b10b6c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6ca914c>
23:40:19.779745 call      2332     def test_view_credit_wallet(self):
23:40:19.780999 line      2333         print('[ * ] View Credit Wallet')
23:40:19.781137 line      2334         _view_credit_wallet = self.ewallet_controller(
23:40:19.781242 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b1ab4c>]}
23:40:19.811394 line      2337         print(str(_view_credit_wallet) + '\n')
23:40:19.811593 line      2338         return _view_credit_wallet
23:40:19.811737 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b1ab4c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6d2b72c>
23:42:06.354745 call      2332     def test_view_credit_wallet(self):
23:42:06.355903 line      2333         print('[ * ] View Credit Wallet')
23:42:06.356041 line      2334         _view_credit_wallet = self.ewallet_controller(
23:42:06.356147 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6adeaec>]}
23:42:06.388331 line      2337         print(str(_view_credit_wallet) + '\n')
23:42:06.388541 line      2338         return _view_credit_wallet
23:42:06.388685 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6adeaec>]}
Starting var:.. self = <__main__.EWallet object at 0xb6c4e10c>
23:42:50.244731 call      2332     def test_view_credit_wallet(self):
23:42:50.245811 line      2333         print('[ * ] View Credit Wallet')
23:42:50.245948 line      2334         _view_credit_wallet = self.ewallet_controller(
23:42:50.246051 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6abfb6c>]}
23:42:50.277384 line      2337         print(str(_view_credit_wallet) + '\n')
23:42:50.277596 line      2338         return _view_credit_wallet
23:42:50.277738 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6abfb6c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6d0a18c>
23:43:58.936668 call      2332     def test_view_credit_wallet(self):
23:43:58.938230 line      2333         print('[ * ] View Credit Wallet')
23:43:58.938490 line      2334         _view_credit_wallet = self.ewallet_controller(
23:43:58.938674 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b7ab4c>]}
23:43:58.972496 line      2337         print(str(_view_credit_wallet) + '\n')
23:43:58.972738 line      2338         return _view_credit_wallet
23:43:58.972907 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b7ab4c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6d4afcc>
23:47:18.362614 call      2332     def test_view_credit_wallet(self):
23:47:18.363844 line      2333         print('[ * ] View Credit Wallet')
23:47:18.364009 line      2334         _view_credit_wallet = self.ewallet_controller(
23:47:18.364119 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6afca8c>]}
23:47:18.394551 line      2337         print(str(_view_credit_wallet) + '\n')
23:47:18.394752 line      2338         return _view_credit_wallet
23:47:18.394936 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6afca8c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6ce51ec>
23:51:55.974694 call      2332     def test_view_credit_wallet(self):
23:51:55.975910 line      2333         print('[ * ] View Credit Wallet')
23:51:55.976178 line      2334         _view_credit_wallet = self.ewallet_controller(
23:51:55.976322 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b56b8c>]}
23:51:56.014653 line      2337         print(str(_view_credit_wallet) + '\n')
23:51:56.014882 line      2338         return _view_credit_wallet
23:51:56.015030 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b56b8c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6c9e1ac>
23:54:03.804560 call      2332     def test_view_credit_wallet(self):
23:54:03.805654 line      2333         print('[ * ] View Credit Wallet')
23:54:03.805791 line      2334         _view_credit_wallet = self.ewallet_controller(
23:54:03.805897 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b0db6c>]}
23:54:03.843179 line      2337         print(str(_view_credit_wallet) + '\n')
23:54:03.843667 line      2338         return _view_credit_wallet
23:54:03.844164 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b0db6c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6c9618c>
23:55:38.797291 call      2332     def test_view_credit_wallet(self):
23:55:38.798491 line      2333         print('[ * ] View Credit Wallet')
23:55:38.798624 line      2334         _view_credit_wallet = self.ewallet_controller(
23:55:38.798724 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b07bcc>]}
23:55:38.833972 line      2337         print(str(_view_credit_wallet) + '\n')
23:55:38.834176 line      2338         return _view_credit_wallet
23:55:38.834409 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b07bcc>]}
Starting var:.. self = <__main__.EWallet object at 0xb6d92fcc>
00:00:27.929258 call      2332     def test_view_credit_wallet(self):
00:00:27.930369 line      2333         print('[ * ] View Credit Wallet')
00:00:27.930658 line      2334         _view_credit_wallet = self.ewallet_controller(
00:00:27.930785 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b83aac>]}
00:00:27.964970 line      2337         print(str(_view_credit_wallet) + '\n')
00:00:27.965389 line      2338         return _view_credit_wallet
00:00:27.965559 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b83aac>]}
Starting var:.. self = <__main__.EWallet object at 0xb6d0e0ac>
00:02:12.217804 call      2332     def test_view_credit_wallet(self):
00:02:12.218913 line      2333         print('[ * ] View Credit Wallet')
00:02:12.219052 line      2334         _view_credit_wallet = self.ewallet_controller(
00:02:12.219159 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6af5bcc>]}
00:02:12.251362 line      2337         print(str(_view_credit_wallet) + '\n')
00:02:12.251722 line      2338         return _view_credit_wallet
00:02:12.251959 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6af5bcc>]}
Starting var:.. self = <__main__.EWallet object at 0xb6d940ec>
00:04:26.325620 call      2332     def test_view_credit_wallet(self):
00:04:26.327077 line      2333         print('[ * ] View Credit Wallet')
00:04:26.327213 line      2334         _view_credit_wallet = self.ewallet_controller(
00:04:26.327316 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b45a6c>]}
00:04:26.358772 line      2337         print(str(_view_credit_wallet) + '\n')
00:04:26.359113 line      2338         return _view_credit_wallet
00:04:26.359291 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b45a6c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6d07d0c>
00:05:52.926269 call      2332     def test_view_credit_wallet(self):
00:05:52.927506 line      2333         print('[ * ] View Credit Wallet')
00:05:52.927645 line      2334         _view_credit_wallet = self.ewallet_controller(
00:05:52.927749 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6ab9acc>]}
00:05:52.963445 line      2337         print(str(_view_credit_wallet) + '\n')
00:05:52.963649 line      2338         return _view_credit_wallet
00:05:52.963790 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6ab9acc>]}
Starting var:.. self = <__main__.EWallet object at 0xb6d68d6c>
00:27:13.002659 call      2332     def test_view_credit_wallet(self):
00:27:13.003924 line      2333         print('[ * ] View Credit Wallet')
00:27:13.004066 line      2334         _view_credit_wallet = self.ewallet_controller(
00:27:13.004167 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b59d0c>]}
00:27:13.034870 line      2337         print(str(_view_credit_wallet) + '\n')
00:27:13.035092 line      2338         return _view_credit_wallet
00:27:13.035235 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b59d0c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6d0140c>
00:31:48.914574 call      2332     def test_view_credit_wallet(self):
00:31:48.915848 line      2333         print('[ * ] View Credit Wallet')
00:31:48.916179 line      2334         _view_credit_wallet = self.ewallet_controller(
00:31:48.916349 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6af2d4c>]}
00:31:48.945859 line      2337         print(str(_view_credit_wallet) + '\n')
00:31:48.946284 line      2338         return _view_credit_wallet
00:31:48.946456 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6af2d4c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6cf894c>
00:36:42.942337 call      2332     def test_view_credit_wallet(self):
00:36:42.943725 line      2333         print('[ * ] View Credit Wallet')
00:36:42.943917 line      2334         _view_credit_wallet = self.ewallet_controller(
00:36:42.944026 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6ae9ccc>]}
00:36:42.974226 line      2337         print(str(_view_credit_wallet) + '\n')
00:36:42.974432 line      2338         return _view_credit_wallet
00:36:42.974575 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6ae9ccc>]}
Starting var:.. self = <__main__.EWallet object at 0xb6d8144c>
00:38:44.167599 call      2332     def test_view_credit_wallet(self):
00:38:44.168907 line      2333         print('[ * ] View Credit Wallet')
00:38:44.169039 line      2334         _view_credit_wallet = self.ewallet_controller(
00:38:44.169143 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b7606c>]}
00:38:44.197845 line      2337         print(str(_view_credit_wallet) + '\n')
00:38:44.198051 line      2338         return _view_credit_wallet
00:38:44.198207 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b7606c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6d0644c>
00:39:44.601374 call      2332     def test_view_credit_wallet(self):
00:39:44.602512 line      2333         print('[ * ] View Credit Wallet')
00:39:44.602648 line      2334         _view_credit_wallet = self.ewallet_controller(
00:39:44.602755 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6afa08c>]}
00:39:44.633348 line      2337         print(str(_view_credit_wallet) + '\n')
00:39:44.633634 line      2338         return _view_credit_wallet
00:39:44.633856 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6afa08c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6cec40c>
00:42:09.085122 call      2332     def test_view_credit_wallet(self):
00:42:09.086447 line      2333         print('[ * ] View Credit Wallet')
00:42:09.086610 line      2334         _view_credit_wallet = self.ewallet_controller(
00:42:09.086716 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6ae104c>]}
00:42:09.115970 line      2337         print(str(_view_credit_wallet) + '\n')
00:42:09.116180 line      2338         return _view_credit_wallet
00:42:09.116322 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6ae104c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6d0b44c>
00:42:51.501522 call      2332     def test_view_credit_wallet(self):
00:42:51.502642 line      2333         print('[ * ] View Credit Wallet')
00:42:51.502778 line      2334         _view_credit_wallet = self.ewallet_controller(
00:42:51.502906 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6ac102c>]}
00:42:51.534030 line      2337         print(str(_view_credit_wallet) + '\n')
00:42:51.534503 line      2338         return _view_credit_wallet
00:42:51.534707 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6ac102c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6d4be0c>
00:43:33.790246 call      2332     def test_view_credit_wallet(self):
00:43:33.791595 line      2333         print('[ * ] View Credit Wallet')
00:43:33.791733 line      2334         _view_credit_wallet = self.ewallet_controller(
00:43:33.791836 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b3f04c>]}
00:43:33.822681 line      2337         print(str(_view_credit_wallet) + '\n')
00:43:33.822931 line      2338         return _view_credit_wallet
00:43:33.823140 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b3f04c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6d18bcc>
00:46:25.697102 call      2332     def test_view_credit_wallet(self):
00:46:25.698212 line      2333         print('[ * ] View Credit Wallet')
00:46:25.698502 line      2334         _view_credit_wallet = self.ewallet_controller(
00:46:25.698629 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b0ac6c>]}
00:46:25.731959 line      2337         print(str(_view_credit_wallet) + '\n')
00:46:25.732161 line      2338         return _view_credit_wallet
00:46:25.732298 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b0ac6c>]}
Starting var:.. self = <__main__.EWallet object at 0xb6d568ec>
00:49:26.068714 call      2332     def test_view_credit_wallet(self):
00:49:26.070131 line      2333         print('[ * ] View Credit Wallet')
00:49:26.070361 line      2334         _view_credit_wallet = self.ewallet_controller(
00:49:26.070466 line      2335                 controller='user', ctype='action', action='view', view='credit_wallet',
New var:....... _view_credit_wallet = {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b48c6c>]}
00:49:26.099283 line      2337         print(str(_view_credit_wallet) + '\n')
00:49:26.099484 line      2338         return _view_credit_wallet
00:49:26.099630 return    2338         return _view_credit_wallet
Return value:.. {'id': 2, 'client_id': 2, 'reference': 'Credit W...sheet.CreditTransferSheet object at 0xb6b48c6c>]}
