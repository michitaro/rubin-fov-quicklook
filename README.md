# FoV Quicklook

## Abstract
- The image data output from the LSST Cam is enormous.
  - The focal plane of the LSST Cam is packed with 189 CCDs, generating 189 images in a single shot.
  - Each image has a resolution of 4k x 4k pixels, resulting in a total of 3.2 gigapixels per shot.
- A method for inspecting this vast image dataset from the full field down to the pixel level is essential in various scenarios.
- The tool **fov-quicklook** was developed to meet this need and is deployed on the development cluster of USDF.

## Implementation
### Idea
- **fov-quicklook** handles a single composite image that arranges the images from a given LSST Cam shot onto the focal plane.
- This composite image is approximately **64,000 x 64,000 pixels**, making it too large to be directly loaded into a web browser.
- To enable fast display, **fov-quicklook** pre-generates downscaled versions of the image at scales of **1/2, 1/4, 1/8, …, 1/256**, dividing them into appropriately sized square sections (called "tiles"). These tiles are then dynamically delivered to the browser as needed.
- Tile generation requires significant data access and computation, but it is executed in parallel across multiple nodes, enabling completion within a few seconds of a user request.

### Architecture
- **fov-quicklook** is designed as an application running on a **Kubernetes cluster** and operates as a **Phalanx application** on the USDF development cluster.
- It consists of the following key components:
  - **Object Storage**
    - The `raw` image data is stored in object storage.
    - This storage is shared with other applications.
  - **Generator**
    - Multiple generator instances exist within the system.
    - They generate tiles as instructed by the **coordinator**.
  - **Coordinator**
    - Receives user requests and directs **generators** to produce the necessary tiles.
  - **Frontend**
    - Serves static content such as HTML and JavaScript.
    - Delivers tiles to users upon request.

### User Interface
- Users access **fov-quicklook** through a web browser (referred to as **WebUI**).
- **Image Display**
  - The WebUI communicates with the backend of **fov-quicklook** via JavaScript, retrieving image tiles and assembling them into a full focal-plane image.
  - To enhance the perceived speed, tiles with lower resolution (higher downscaling) are loaded first.
  - The WebUI utilizes **WebGL** technology to leverage GPU acceleration when available.
  - Tile pixel data is stored in **float32** format and can be dynamically stretched within the WebUI.
  - Multiple color scales, including **Viridis** and **Cividis**, are implemented.
- **Metadata Access**
  - By right-clicking on an image, users can view the **FITS file header** corresponding to that location or download the **FITS file** itself.

## Performance
- For raw images, display can begin in as fast as **4 seconds**.
  - This time depends on the cluster load.
