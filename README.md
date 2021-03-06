EWallet Credit Clock - Virtual Payment System - Server Core

Hello there!

If you're new around here, feel free to start by execution the EWServerCore
test suit using the following command:

    ~$ python3 -m unittest discover

That alone should get you familiar with the high level instruction sets the
server receives in the form of JSON and the appropriate responses for each
System, Client and Master actions.


EWSC Introduction -


The EWServerCore is the main application of the EWCreditClock Suit,
all other applications belonging to the suit having been built around it, and
are dependent on an instance of the EWServerCore running either locally
or somewhere in the cloud.

The EWCreditClock Suit contains:

    * (EWSC)  | Server Core           | Web Service with REST API   | v.Chronos (Beta)
    * (EWCC)  | Python Client Core    | Importable Library          | v.Chronos (Beta)
    * (EWAT)  | API Tutor             | Tutor Script                | v.Chronos (Beta)
    * (EWDWC) | Default Web Client    | Web Portal Application      | TODO
    * (EWDMC) | Default Mobile Client | Android Portal Application  | TODO
    * (EWJCC) | Java Client Core      | Importable Library          | TODO


EWSC Description -


But whats all this about anyway?

Well you see, the EWServerCore serves as a virtual payment system in the cloud,
and supports transactions with both credits and time (by converting the paid
for credits to time, obviously).

This makes it an ideal choice for it beeing used as both a credit wallet in the
sky as well as a professional software licensing option.


EWSC Controllers -


This might get a little techy, but the EWServerCore has 3 main interfaces, only
two of which can be accesed through the REST API:

    * (System Controller) | Private | Server management actions and events
    * (Master Controller) | Public  | Master user account actions and events
    * (Client Controller) | Public  | Client application actions and events

    [ NOTE ]: Subordonate user account actions and events are handled by the
              Client Controller as they are initiated by the client application.

Following a B2B business model, the Master accounts are created by the party
offering the EWCreditClock service to their clients, along with a certificate
used for authentication in all their software products.

Master accounts can only hold a set number of Subordonate accounts, details of
which are found in the payment plan.

The Subordonate accounts are the end-user accounts, usually the clients of the
comercial entity owning a Master account.

System actions and events require no account or session, as they are only used
behind the REST API for server core administration and automation.


EWSC Fun Facts! -


    * The entire EWalletCreditClock suit was coded in a custom made IDE using
      Vim, Tmux and CLI Git on a Debian based distribution using the GNOME
      desktop environment. (Not kidding, where there's a shell there's a way)

    * The EW motto is Pay Only When You're On The Clock, and not when you're off it.
      (Still working on this one, seems kind of a mouthful to me)

    * The client can orphan sessions by requesting a new session token with an
      old client id. (I know, I know, but its a fun fact to me)


EWSC Contribuitors -


    * S:Mx093pk01 - Core Developer and Designer
    * M:So093pk02 - Technology Advisor
    * G:Ec093pk03 - Quality Assurance
    * M:Mi093pk04 - Business Advisor
    * U:Si093pk05 - Graphic Design and Artwork


Regards, the Alveare Solutions society.

