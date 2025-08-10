# Image-based road width measurements
This repository has been made for a Bachelor's thesis, focused on extracting spatial data from images in Assetto Corsa. 

## In-game app setup
To start the image capture, firstly the project folder needs to be uploaded to the Steam's Assetto Corsa (AC) apps folder. The final path should look like this: `Steam\steamapps\common\assettocorsa\apps\python\image_capture`.
Then open AC navigate to the Main Menu -> Options -> General -> UI Modules and tick the box next to the image_capture in-game app.

Then choose the light gray Mercedes SLS AMG as your car and a track to your liking. You can choose whichever type of race to capture the images from. This code currently only supports the Nurburgring GP track, however more tracks can be added by following the tutorial mentioned in their README under the 3rd step: [Link](https://github.com/dasGringuen/assetto_corsa_gym) (It is also necessary to download their codebase).
* Make sure to add the generated truth data `csv` file to the `truthData` folder
The weather conditions should be set to `Clear`.

## External image capture
Before the images can be captured make sure you are using a Python 3.10.12 version, create a venv `& "path_to_python/python.exe" -m venv venv`, activate the venv with `venv/Scripts/activate`, download the required packages from the `requirements.txt` file with `pip install -r requirements.txt`.
* Open an external terminal supported by your operating system and naviagte to the `image_capture` folder
* Run this in the `image_capture` folder `python dataGathering/external_capture.py`
* A 30-second countdown is then intiazised before the images are captured
* Start the game
* The images are captured until the terminal window is closed or interrupted from the keyboard (`Ctrl + C` for Windows).
* The collected images are saved to the `data/images` folder with the exact time and date the collection started

* It is HIGHLY SUGGESTED to remove any images that do not have a clear view of the racetrack before continuing.

### Check for proper functioning
After the images have been captured `image_capture` application should have saved the data about the car's location into the `data/csv` folder with the time, date stamp the corresponding images folder has
If the `.csv` file was populated with data then everything works. If not check the following:
* Is the `image_capture` in-game app activated by checking the box in the settings

## Post data-gathering
Before moving on make sure to remove any images that are not properly captured and the corresponding data points from the populated csv named `timestamp.csv`. Once this is done proceed to the `main.py` file and run it (will take a few hours to run, however does depend on the amount of images).
* The game gathered data includes the following:
  * timestamp - the timestamp when the image was taken
  * lap_position - position from 0 to 1 on the track, with 0 being the start and 1 being the finish
  * pos_x - the x-coordinates of the car
  * pos_y - the y-coordinates of the car
  * filename - the name of the image file from which the data was gathered from

This will take the latest image folder and process all the images. If the latest image folder is not desired follow the instructions in the `main.py` file.
* Processed images can be found in the `data/processedImgaes` folder that will have the same timestamp as the images.
  * These images will have the road edges marked with coloured dots for visual verification.
* Measured data from the images will be found in the `data/csv` folder in the `measured_data.csv`.
  * The measured data includes:
    * filename - name of the image
    * road_width - measured road width
    * distance_left - the measured distance to the left track boundary
    * distance_right - the measured to distance the right track boundary
    * car_center - the pixel values of the center of the car on the image

## Analyzing results
### Addtional images and data points
Firstly, a check is made against whether there are any measured data points that do not have a corresponding image and the other way around. Make sure to go over the list and delete any items that are highlighted.

### Merging CSV files
Secondly, the game gathered data and the measured data will be merged together. Afterwards the previously merged file is merged with the truth data file. This is all done in the background and only a final `merged_datasets.csv` file is saved to the `data/csv/{timestamp}` folder.

### Analyzing results
Once the data is merged together, the performance metrics - MAPE, R-squared, Pearson's correlation coefficient - are calculated and printed out. The data is also stored in the `results.csv` file.

To also receive data on how the model performed on specific parts of the track (straight, right turns, left turns) some manual work needs to be done.
* At the top of `analyse_results.py` file are a few examples how to categorise images into different sections on the racetrack. 
  * The numbers indicate the image position in the images' folder.
  * First image has a number 1, tenth image corresponds to a number 10, etc.
* If your images do not have a specific part of the racetrack (for example, no right turns), then mark that section with an empty list.

Once you are done with this, re-run the `main.py` file, indicate that you have segmented the areas of the racetrack, and the performance metrics will be calculated for each of the racetrack sections. An additional file with image specific performance metrics will be generated called `road_type_results.csv`.

