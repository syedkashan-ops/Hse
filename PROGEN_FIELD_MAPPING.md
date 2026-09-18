# ProGen V1 Field Mapping Notes

Based on the supplied screenshots, the observed workflow includes:

## Initial workflow

- Welcome / HSE ProGen portal
- IR / SOR Investigation Portal
- Pending Acknowledgement
- First Incident Report
- Move To Investigation Report

## First Incident Report — visible concepts

The screenshots show sections/fields relating to:
- Reference number
- Incident type
- Reported date/time
- Incident date/time
- Location
- Incident description
- Immediate response taken
- Incident severity
- Incident probability
- Incident risk rating
- Incident types
- Weather / incident location context

The exact HTML control names, IDs and dropdown option values must be read from the
live logged-in application before hard-coded automation is added.

## Investigation Report — visible tabs/sections

The screenshots show:
- Consequence Details
- Finding Summary
- Chronology
- Contributing Factors (CLC)
- Similar Past Incidents
- Why Why Analysis Tree
- Causes
- Actions and Recommendations
- Lesson Learned
- Risk Assessment
- Regulatory & Statutory Notification
- Evidence & Attachments
- Corrective Training
- Executive Summary

## Design principle

The AI should use the existing incident as the starting source and ask for verification
when evidence is insufficient. It should not turn assumptions into official findings.
