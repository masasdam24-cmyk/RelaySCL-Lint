<?xml version="1.0" encoding="UTF-8"?>
<SCL xmlns="http://www.iec.ch/61850/2003/SCL" version="2007" revision="B">
  <Header id="synthetic-valid-example"/>
  <Communication>
    <SubNetwork name="SubstationLAN" type="8-MMS">
      <ConnectedAP iedName="PROTECTION_A" apName="AP1">
        <GSE ldInst="LD0" cbName="gcbTrip">
          <Address>
            <P type="MAC-Address">01-0C-CD-01-00-01</P>
            <P type="APPID">0001</P>
            <P type="VLAN-ID">000</P>
            <P type="VLAN-PRIORITY">4</P>
          </Address>
          <MinTime unit="s" multiplier="m">4</MinTime>
          <MaxTime unit="s" multiplier="m">1000</MaxTime>
        </GSE>
      </ConnectedAP>
    </SubNetwork>
  </Communication>
  <IED name="PROTECTION_A" manufacturer="Example" configVersion="1">
    <AccessPoint name="AP1"><Server><LDevice inst="LD0"><LN0 lnClass="LLN0" inst="" lnType="LLN0Type">
      <DataSet name="dsTrip"><FCDA ldInst="LD0" lnClass="PTRC" lnInst="1" doName="Tr" daName="general" fc="ST"/></DataSet>
      <GSEControl name="gcbTrip" type="GOOSE" datSet="dsTrip" appID="trip" confRev="1"/>
    </LN0></LDevice></Server></AccessPoint>
  </IED>
</SCL>
