# Aero Data Front End

Update your CUP file with the latest airports, with the latest airport data available on [OpenAIP](https://www.openaip.net). Airports in the file must be marked using one of the styles designated for the airports in the [CUP specification](https://github.com/naviter/seeyou_file_formats/blob/main/CUP_file_format.md). 

The service will update the following fields:
- Country
- Elevation
- Style: Based on the main runway of the airport
- Runway Direction, Length, Width
- Frequency

**Options:**
- *Update airport locations:* Updates the location of the airports stored in your CUP file, can cause your tasks to change. **ON by default**
- *Add missing airports:* This will create an imaginary rectangle around all your points and add airports that you might not have in your CUP.
- *Remove closed airports:* This will remove any airports that are marked CLOSED in the OpenAIP from your file.
