/**
 * Implementation example:
 * 		http://docs.opencv.org/doc/tutorials/objdetect/cascade_classifier/cascade_classifier.html#cascade-classifier
 * Cascade Classification documentation:
 * 		http://docs.opencv.org/modules/objdetect/doc/cascade_classification.html#haar-feature-based-cascade-classifier-for-object-detection
 * 	Cascade Classifier Training:
 * 		http://docs.opencv.org/doc/user_guide/ug_traincascade.html
 */
#include <ostream>
#include <iostream>
#include <fstream>
#include <boost/filesystem.hpp>
#include <opencv2/imgproc/imgproc.hpp>

#include "Adaboost.h"

/**
 * Reads the images in the specified directory and processes them.
 *
 * @param directory The relative path to the directory.
 */
void Adaboost::readDirectory(const std::string& img_dir, const std::string& save_dir, const std::string& detections_file, const std::string& classifier_file) {
	// Specify the path as the directory being read.
	// Create variables to store the image and file name.

	if (!boost::filesystem::exists(img_dir)) {
		std::cerr << img_dir << " does not exist." << std::endl;
	}

	// Attempt to load the specified classifier.
	if (cascadeClassifier.load(classifier_file)) {
		// cv::Mat frame;
		// std::string file;
		// // Iterate through every image in the directory. It attempts to read the file and exits the loop if no image
		// // was read. This is an alternative to using the boost library.
		// for (int i = 1; !(frame = cv::imread(img_dir + "/" + (file = getFileName(i)), Image.flag)).empty(); i++) {
		// 	std::cout << "Processing frame " << i << "." << std::endl;
		// 	// Process the current frame.
		// 	processFrame(frame, file, detections_file);
		// }

		boost::filesystem::directory_iterator end_itr; // default construction yields past-the-end
		for (boost::filesystem::directory_iterator itr(img_dir); itr != end_itr; ++itr) {
			if (boost::filesystem::is_directory(itr->status())) {
				// TODO: Consider allowing recursion.
				// if (boost::filesystem::find_file(itr->path(), file_name, path_found))
				// 	return true;
			} else {
				auto curr_img_path = itr->path().string();
				auto curr_img_name = itr->path().leaf().string();

				auto frame = cv::imread(curr_img_path, Image.flag);
				if (!frame.empty()) {
					std::cout << "Processing '" << curr_img_path << "'" << std::endl;
					processFrame(frame, curr_img_name, save_dir, detections_file);
				} else {
					std::cerr << "Could not process '" << curr_img_path << "'" << std::endl;
				}
			}
		}
	} else {
		std::cerr << "Unable to load the cascade classifier." << std::endl;
	}
}


/**
 * Retrieves the file name based on the index within the sequence of images.
 *
 * @param index The current frame within the sequence.
 */
inline std::string Adaboost::getFileName(int index) {
	return Image.prefix + std::to_string(index) + "." + Image.format;
}

/**
 * Appends the detected object positions to a file with the given name.
 *
 * @param img_file Image file name.
 * @param objs Detected objects.
 * @param detections_file File to save detections to.
 */
void saveDetections(std::string img_file, std::vector<cv::Rect> objs, std::string detections_file) {
	std::ofstream fs(detections_file, std::ios::out | std::ios::app);
	fs << img_file;
	fs << " " << objs.size();
	for (auto r : objs) {
		fs << " " << r.x
		   << " " << r.y
		   << " " << r.width
		   << " " << r.height;
	}
	fs << std::endl;
	fs.close();
}

/**
 * Processes a frame by converting it to grayscale and applying an equalizing histogram. Objects are then detected in
 * the frame and the processed image is saved.
 *
 * @param frame The current image.
 * @param file The name of the file.
 */
void Adaboost::processFrame(cv::Mat& frame, std::string file_name, std::string save_dir, std::string detections_file) {
	// Create an image container to store the processed frame.
	cv::Mat processedFrame;
	// Convert the frame to grayscale and store it in the new container so it can be processed more efficiently.
	cvtColor(frame, processedFrame, CV_BGR2GRAY);
	// Apply a histogram equalization to improve the image contrast.
	//cv::equalizeHist(processedFrame, processedFrame);
	// Detect the objects in the frame.
	auto objs = detectObjects(frame, processedFrame);
	// Save the frame.
	saveFrame(frame, save_dir, file_name);

	saveDetections(file_name, objs, detections_file);
}

/**
 * Detects objects using the cascade classifier and the processed frame. This method also outputs the detection on
 * the original image.
 *
 * @param frame The original image.
 * @param processedFrame The processed image used with the classifier.
 */
std::vector<cv::Rect> Adaboost::detectObjects(cv::Mat& frame, cv::Mat& processedFrame) {
	// Create a vector of rectangles to store the detected objects.
	std::vector<cv::Rect> objects;
	// Detect the objects using the processed frame and store the results in objects.
	cascadeClassifier.detect(processedFrame, objects);
	// Iterate through every detection.
	for (size_t i = 0, len = objects.size(); i < len; i++) {
		// Get the current object.
		cv::Rect object = objects[i];
		// Calculate the size and center of the object.
		cv::Point center((int) (object.x + object.width * 0.5), (int) (object.y + object.height * 0.5));
		cv::Size size((int) (object.width * 0.5), (int) (object.height * 0.5));
		// Display the detection on the coloured frame.
		displayDetection(frame, center, size);
	}

	return objects;
}

/**
 * Saves a processed frame into a subdirectory.
 *
 * @param frame The image that is being saved.
 * @param file The file name of the image.
 */
inline void Adaboost::saveFrame(cv::Mat& frame, std::string save_dir, std::string file_name) {
	std::string save_path = save_dir + "/" + file_name;

	if (cv::imwrite(save_path, frame)) {
		std::cout << "    Saved image '" << save_path << "'" << std::endl;
	} else {
		std::cerr << "    Could not save '" << save_path << "'" << std::endl;
	}
}

// /**
//  * Returns the directory where saved images will be stored.
//  */
// inline std::string Adaboost::getSaveDirectory() {
// 	return path + "/processed";
// }

/**
 * Displays a detection on the specified image by drawing an ellipse in the given position.
 *
 * @param frame An image container that stores the image that has found a detection.
 * @param center The center point of the detection.
 * @param size The size of the sphere.
 */
inline void Adaboost::displayDetection(cv::Mat& frame, cv::Point center, cv::Size size) {
	cv::ellipse(frame, center, size, Draw.angle, Draw.startAngle, Draw.endAngle, Draw.color, Draw.thickness, Draw.lineType, Draw.shift);
}
