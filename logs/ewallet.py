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
