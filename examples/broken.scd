<?xml version="1.0" encoding="UTF-8"?>
<SCL xmlns="http://www.iec.ch/61850/2003/SCL">
  <Communication>
    <SubNetwork name="LAN"><ConnectedAP iedName="PROTECTION_A" apName="AP1">
      <GSE ldInst="LD0" cbName="gcbTrip"><Address>
        <P type="MAC-Address">AA-BB</P>
        <P type="APPID">ZZZZ</P>
        <P type="VLAN-PRIORITY">9</P>
      </Address></GSE>
    </ConnectedAP></SubNetwork>
  </Communication>
  <IED name="PROTECTION_A"><AccessPoint name="AP1"><Server><LDevice inst="LD0"><LN0>
    <GSEControl name="gcbTrip" datSet="dsMissing" confRev="0"/>
  </LN0></LDevice></Server></AccessPoint></IED>
</SCL>
