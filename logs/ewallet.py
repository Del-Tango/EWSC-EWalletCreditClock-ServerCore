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
