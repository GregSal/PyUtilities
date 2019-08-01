<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="2.0" xmlns:xml="http://www.w3.org/XML/1998/namespace" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:xs="http://www.w3.org/2001/XMLSchema" exclude-result-prefixes=" xml xsl xs">
<xsl:output method="xml" omit-xml-declaration="no" indent="yes" />


    <xsl:template match="/">
        <!-- **TODO** DEFINE YOUR XSLT TRANSFORM -->
        <RootElement>
            <xsl:for-each select="GuiDefinition/VariableSet">
                <ChildElement>
                    <xsl:value-of select="." />
                </ChildElement>
    	     </xsl:for-each>
        </RootElement>
    </xsl:template>
</xsl:stylesheet>