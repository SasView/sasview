<?xml version="1.0"?>

<!--
########### SVN repository information ###################
# $Date$
# $Author$
# $Revision$
# $HeadURL$
# $Id$
########### SVN repository information ###################

Purpose:
	This stylesheet is used to translate cansas1d:1.1
	XML data files into a display form for viewing
	in a web browser such as Firefox or Internet Explorer
	that supports client-side XSLT formatting.

Usage:
	xsltproc cansas1d.xsl datafile.xml > datafile.html
	(or include it as indicated at the documentation site
	http://www.cansas.org/wgwiki/index.php/cansas1d_documentation)

Copyright (c) 2013, UChicago Argonne, LLC
This file is distributed subject to a Software License Agreement found
in the file LICENSE that is included with this distribution. 
-->

<xsl:stylesheet version="1.1"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	xmlns:cs="urn:cansas1d:1.1"
	xmlns:fn="http://www.w3.org/2005/02/xpath-functions"
	>

	<xsl:template match="/">
<!-- DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd" -->
		<html>
			<head>
				<title>SAS data in canSAS 1-D format</title>
			</head>
			<body>
				<h1>SAS data in canSAS 1-D format</h1>
				<small>generated using <TT>cansas1d.xsl</TT> from canSAS</small>
				<BR />
				<table border="2">
					<tr>
						<th bgcolor="lavender">canSAS 1-D XML version:</th>
						<td><xsl:value-of select="cs:SASroot/@version" /></td>
					</tr>
					<tr>
						<th bgcolor="lavender">number of entries:</th>
						<td><xsl:value-of select="count(cs:SASroot/cs:SASentry)" /></td>
					</tr>
					<xsl:if test="count(/cs:SASroot//cs:SASentry)>1">
						<!-- if more than one SASentry, make a table of contents -->
						<xsl:for-each select="/cs:SASroot//cs:SASentry">
							<tr>
								<th bgcolor="lavender">SASentry-<xsl:value-of select="position()" /></th>
								<td>
									<a href="#SASentry-{generate-id(.)}">
										<xsl:if test="@name!=''">(<xsl:value-of select="@name" />)</xsl:if>
										<xsl:value-of select="cs:Title" />
									</a>
								</td>
								<xsl:if test="count(cs:SASdata)>1">
									<td>
										<!-- if more than one SASdata, make a local table of contents -->
										<xsl:for-each select="cs:SASdata">
											<xsl:if test="position()>1">
												<xsl:text> | </xsl:text>
											</xsl:if>
											<a href="#SASdata-{generate-id(.)}">
												<xsl:choose>
													<xsl:when test="cs:name!=''">
														<xsl:value-of select="cs:name" />
													</xsl:when>
													<xsl:when test="@name!=''">
														<xsl:value-of select="@name" />
													</xsl:when>
													<xsl:otherwise>
														SASdata<xsl:value-of select="position()" />
													</xsl:otherwise>
												</xsl:choose>
											</a>
										</xsl:for-each>
									</td>
								</xsl:if>
							</tr>
						</xsl:for-each>
					</xsl:if>
				</table>
				<xsl:apply-templates  />
				<hr />
				<small><center>$Id$</center></small>
			</body>
		</html>
	</xsl:template>

	<xsl:template match="cs:SASroot">
		<xsl:for-each select="cs:SASentry">
			<hr />
			<br />
			<a id="#SASentry-{generate-id(.)}"  name="SASentry-{generate-id(.)}" />
			<h1>SASentry<xsl:value-of select="position()" />:<xsl:if 
				test="@name!=''">(<xsl:value-of select="@name" />)</xsl:if>
				<xsl:value-of select="cs:Title" /></h1>
			<xsl:if test="count(cs:SASdata)>1">
				<table border="2">
					<caption>SASdata contents</caption>
					<xsl:for-each select="cs:SASdata">
						<tr>
							<th>SASdata-<xsl:value-of select="position()" /></th>
							<td>
								<a href="#SASdata-{generate-id(.)}">
									<xsl:choose>
									<xsl:when test="@name!=''">
											<xsl:value-of select="@name" />
										</xsl:when>
										<xsl:otherwise>
											SASdata<xsl:value-of select="position()" />
										</xsl:otherwise>
									</xsl:choose>
								</a>
							</td>
						</tr>
					</xsl:for-each>
				</table>
			</xsl:if>
			<br />
			<table border="2">
				<tr>
					<th>SAS data</th>
					<xsl:for-each select="cs:SAStransmission_spectrum"><th>transmission spectrum: <xsl:value-of select="@name" /></th></xsl:for-each>
					<th>Selected Metadata</th>
				</tr>
				<tr>
					<td valign="top"><xsl:apply-templates  select="cs:SASdata" /></td>
					<xsl:apply-templates  select="cs:SAStransmission_spectrum" />
					<td valign="top">
						<table border="2">
							<tr bgcolor="lavender">
								<th>name</th>
								<th>value</th>
								<th>unit</th>
							</tr>
							<tr>
								<td>Title</td>
								<td><xsl:value-of select="cs:Title" /></td>
								<td />
							</tr>
							<tr>
								<td>Run</td>
								<td><xsl:value-of select="cs:Run" /></td>
								<td />
							</tr>
							<tr><xsl:apply-templates  select="run" /></tr>
							<xsl:apply-templates  select="cs:SASsample" />
							<xsl:apply-templates  select="cs:SASinstrument" />
							<xsl:apply-templates  select="cs:SASprocess" />
							<xsl:apply-templates  select="cs:SASnote" />
						</table>
					</td>
				</tr>
			</table>
		</xsl:for-each>
	</xsl:template>

	<xsl:template match="cs:SAStransmission_spectrum">
		<td valign="top">
		    <table border="2">
			<caption><xsl:if 
				test="@name!=''"><xsl:value-of select="@name" /></xsl:if> (<xsl:value-of 
				select="count(cs:Tdata)" /> points)
				<a id="#Tdata-{generate-id(.)}"  name="Tdata-{generate-id(.)}" />
			</caption>
			<tr bgcolor="lavender">
				<xsl:for-each select="cs:Tdata[1]/*">
					<th>
						<xsl:value-of select="name()" /> 
						<xsl:if test="@unit!=''"> (<xsl:value-of select="@unit" />)</xsl:if>
					</th>
				</xsl:for-each>
			</tr>
		    	<xsl:for-each select="cs:Tdata">
					<tr>
						<xsl:for-each select="*">
							<xsl:call-template name="td-value"/>
						</xsl:for-each>
					</tr>
				</xsl:for-each>
			</table>
		</td>
	</xsl:template>

	<xsl:template match="cs:SASdata">
		<a id="#SASdata-{generate-id(.)}"  name="SASdata-{generate-id(.)}" />
		<table border="2">
			<caption><xsl:if 
				test="@name!=''"><xsl:value-of select="@name" /></xsl:if> (<xsl:value-of 
				select="count(cs:Idata)" /> points)</caption>
			<tr bgcolor="lavender">
				<xsl:for-each select="cs:Idata[1]/*">
					<th>
						<xsl:value-of select="name()" /> 
						<xsl:if test="@unit!=''"> (<xsl:value-of select="@unit" />)</xsl:if>
					</th>
				</xsl:for-each>
			</tr>
			<xsl:for-each select="cs:Idata">
				<tr>
					<xsl:for-each select="*">
						<xsl:call-template name="td-value"/>
					</xsl:for-each>
				</tr>
			</xsl:for-each>
		</table>
	</xsl:template>

	<xsl:template match="cs:SASsample">
		<tr>
			<td>SASsample</td>
			<td><xsl:value-of select="@name" /></td>
			<td />
		</tr>
		<xsl:for-each select="*">
			<xsl:choose>
				<xsl:when test="name()='position'">
					<xsl:apply-templates select="." />
				</xsl:when>
				<xsl:when test="name()='orientation'">
					<xsl:apply-templates select="." />
				</xsl:when>
				<xsl:otherwise>
					<xsl:call-template name="tr-parent-value-units"/>
				</xsl:otherwise>
			</xsl:choose>
		</xsl:for-each>
	</xsl:template>

	<xsl:template match="cs:SASinstrument">
		<tr>
			<td>SASinstrument</td>
			<td><xsl:value-of select="cs:name" /></td>
			<td><xsl:value-of select="@name" /></td>
		</tr>
		<xsl:for-each select="*">
			<xsl:choose>
				<xsl:when test="name()='SASsource'"><xsl:apply-templates select="." /></xsl:when>
				<xsl:when test="name()='SAScollimation'"><xsl:apply-templates select="." /></xsl:when>
				<xsl:when test="name()='SASdetector'"><xsl:apply-templates select="." /></xsl:when>
				<xsl:when test="name()='name'" />
				<xsl:otherwise>
					<xsl:call-template name="tr-parent-value-units"/>
				</xsl:otherwise>
			</xsl:choose>
		</xsl:for-each>
	</xsl:template>

	<xsl:template match="cs:SASsource">
		<tr>
			<td><xsl:value-of select="name()" /></td>
			<td><xsl:value-of select="@name" /></td>
			<td />
		</tr>
		<xsl:for-each select="*">
			<xsl:choose>
				<xsl:when test="name()='beam_size'"><xsl:apply-templates select="." /></xsl:when>
				<xsl:otherwise>
					<xsl:call-template name="tr-parent-value-units"/>
				</xsl:otherwise>
			</xsl:choose>
		</xsl:for-each>
	</xsl:template>

	<xsl:template match="cs:beam_size">
		<xsl:call-template name="tr-parent-name"/>
		<xsl:for-each select="*">
			<xsl:call-template name="tr-grandparent-value-units"/>
		</xsl:for-each>
	</xsl:template>

	<xsl:template match="cs:SAScollimation">
		<xsl:for-each select="*">
			<xsl:choose>
				<xsl:when test="name()='aperture'"><xsl:apply-templates select="." /></xsl:when>
				<xsl:otherwise>
					<xsl:call-template name="tr-parent-value-units"/>
				</xsl:otherwise>
			</xsl:choose>
		</xsl:for-each>
	</xsl:template>

	<xsl:template match="cs:aperture">
		<tr>
			<td><xsl:value-of select="name(..)" />_<xsl:value-of select="name()" /></td>
			<td><xsl:value-of select="@name" /></td>
			<td><xsl:value-of select="@type" /></td>
		</tr>
		<xsl:for-each select="*">
			<xsl:choose>
				<xsl:when test="name()='size'"><xsl:apply-templates select="." /></xsl:when>
				<xsl:otherwise>
					<xsl:call-template name="tr-grandparent-value-units"/>
				</xsl:otherwise>
			</xsl:choose>
		</xsl:for-each>
	</xsl:template>

	<xsl:template match="cs:size">
		<tr>
			<xsl:call-template name="td-grandparent"/>
			<td><xsl:value-of select="@name" /></td>
			<td />
		</tr>
		<xsl:for-each select="*">
			<tr>
				<xsl:call-template name="td-greatgrandparent"/>
				<xsl:call-template name="td-value"/>
				<xsl:call-template name="td-unit"/>
			</tr>
		</xsl:for-each>
	</xsl:template>

	<xsl:template match="cs:SASdetector">
		<tr>
			<td><xsl:value-of select="name()" /></td>
			<td><xsl:value-of select="cs:name" /></td>
			<td><xsl:value-of select="@name" /></td>
		</tr>
		<xsl:for-each select="*">
			<xsl:choose>
				<xsl:when test="name()='name'" />
				<xsl:when test="name()='offset'"><xsl:apply-templates select="." /></xsl:when>
				<xsl:when test="name()='orientation'"><xsl:apply-templates select="." /></xsl:when>
				<xsl:when test="name()='beam_center'"><xsl:apply-templates select="." /></xsl:when>
				<xsl:when test="name()='pixel_size'"><xsl:apply-templates select="." /></xsl:when>
				<xsl:otherwise>
					<xsl:call-template name="tr-parent-value-units"/>
				</xsl:otherwise>
			</xsl:choose>
		</xsl:for-each>
	</xsl:template>

	<xsl:template match="cs:orientation">
		<xsl:call-template name="tr-parent-name"/>
		<xsl:for-each select="*">
			<xsl:call-template name="tr-grandparent-value-units"/>
		</xsl:for-each>
	</xsl:template>

	<xsl:template match="cs:position">
		<xsl:call-template name="tr-parent-name"/>
		<xsl:for-each select="*">
			<xsl:call-template name="tr-grandparent-value-units"/>
		</xsl:for-each>
	</xsl:template>

	<xsl:template match="cs:offset">
		<xsl:call-template name="tr-parent-name"/>
		<xsl:for-each select="*">
			<xsl:call-template name="tr-grandparent-value-units"/>
		</xsl:for-each>
	</xsl:template>

	<xsl:template match="cs:beam_center">
		<xsl:call-template name="tr-parent-name"/>
		<xsl:for-each select="*">
			<xsl:call-template name="tr-grandparent-value-units"/>
		</xsl:for-each>
	</xsl:template>

	<xsl:template match="cs:pixel_size">
		<xsl:call-template name="tr-parent-name"/>
		<xsl:for-each select="*">
			<xsl:call-template name="tr-grandparent-value-units"/>
		</xsl:for-each>
	</xsl:template>

	<xsl:template match="cs:term">
		<tr>
			<td><xsl:value-of select="@name" /></td>
			<xsl:call-template name="td-value"/>
			<xsl:call-template name="td-unit"/>
		</tr>
	</xsl:template>

	<xsl:template match="cs:SASprocessnote" mode="standard">
		<tr>
			<td><xsl:value-of select="name()" /></td>
			<xsl:call-template name="td-value"/>
			<td><xsl:value-of select="@name" /></td>
		</tr>
	</xsl:template>
	
	<xsl:template match="cs:SASprocessnote" mode="Indra">
		<!-- 
			Customization for APS USAXS metadata
			These will be IgorPro wavenote variables
		-->
		<xsl:for-each select="cs:APS_USAXS">
			<!-- ignore any other elements at this point -->
			<tr>
				<td bgcolor="lightgrey"><xsl:value-of select="name(..)" /></td>
				<td bgcolor="lightgrey"><xsl:value-of select="name()" /></td>
				<td bgcolor="lightgrey"><xsl:value-of select="@name" /></td>
			</tr>
			<xsl:for-each select="*">
				<tr>
					<td><xsl:value-of select="name()" /></td>
					<xsl:call-template name="td-value"/>
					<td><xsl:value-of select="@name" /></td>
				</tr>
			</xsl:for-each>
		</xsl:for-each>
	</xsl:template>
	
	<xsl:template match="cs:SASprocess">
		<tr>
			<td><xsl:value-of select="name()" /></td>
			<td><xsl:value-of select="cs:name" /></td>
			<td><xsl:value-of select="@name" /></td>
		</tr>
		<xsl:for-each select="*">
			<xsl:choose>
				<xsl:when test="name()='name'" />
				<xsl:when test="name()='term'"><xsl:apply-templates select="." /></xsl:when>
				<xsl:when test="name()='SASprocessnote'">
					<xsl:choose>
						<xsl:when test="../@name='Indra'"><xsl:apply-templates select="." mode="Indra"/></xsl:when>
						<xsl:otherwise><xsl:apply-templates select="." mode="standard"/></xsl:otherwise>
					</xsl:choose>
				</xsl:when>
				<xsl:otherwise>
					<tr>
						<xsl:call-template name="td-grandparent"/>
						<xsl:call-template name="td-value"/>
						<td />
					</tr>
				</xsl:otherwise>
			</xsl:choose>
		</xsl:for-each>
	</xsl:template>

	<xsl:template match="cs:SASnote">
		<xsl:if test="@name!=''">
			<tr>
				<td><xsl:value-of select="name()" /></td>
				<xsl:call-template name="td-value"/>
				<td><xsl:value-of select="@name" /></td>
			</tr>
		</xsl:if>
	</xsl:template>
	
	<!-- =============== convenience routines =============== -->
	
	<xsl:template name="tr-parent-value-units">
		<tr>
			<xsl:call-template name="td-parent"/>
			<xsl:call-template name="td-value"/>
			<xsl:call-template name="td-unit"/>
		</tr>
	</xsl:template>
	
	<xsl:template name="tr-grandparent-value-units">
		<tr>
			<xsl:call-template name="td-grandparent"/>
			<xsl:call-template name="td-value"/>
			<xsl:call-template name="td-unit"/>
		</tr>
	</xsl:template>
	
	<xsl:template name="tr-parent-name">
		<tr>
			<xsl:call-template name="td-parent"/>
			<td><xsl:value-of select="@name" /></td>
			<td />
		</tr>
	</xsl:template>
	
	<xsl:template name="td-value">
		<td><xsl:value-of select="." /></td>
	</xsl:template>
	
	<xsl:template name="td-parent">
		<td><xsl:value-of select="name(..)" 
			/>_<xsl:value-of select="name()" 
			/></td>
	</xsl:template>
	
	<xsl:template name="td-grandparent">
		<td><xsl:value-of select="name(../..)" 
			/>_<xsl:value-of select="name(..)" 
			/>_<xsl:value-of select="name()" 
			/></td>
	</xsl:template>
	
	<xsl:template name="td-greatgrandparent">
		<td><xsl:value-of select="name(../../..)" 
			/>_<xsl:value-of select="name(../..)" 
			/>_<xsl:value-of select="name(..)" 
			/>_<xsl:value-of select="name()" 
			/></td>
	</xsl:template>
	
	<xsl:template name="td-unit">
		<td><xsl:value-of select="@unit" /></td>
	</xsl:template>

</xsl:stylesheet>
