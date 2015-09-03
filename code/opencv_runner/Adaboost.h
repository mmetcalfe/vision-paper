#ifndef OBJECT_DETECTION_ADABOOST_H
#define OBJECT_DETECTION_ADABOOST_H

#include <string>
#include <opencv2/core/core.hpp>
#include <opencv2/highgui/highgui.hpp>
#include "CascadeClassifier.h"

class Adaboost {

	private:

		const struct {
			std::string prefix;
			const std::string format;
			int flag;
		} Image = {"test_", "jpg", CV_LOAD_IMAGE_COLOR};

		const struct {
			const double angle;
			const double startAngle;
			const double endAngle;
			const cv::Scalar color;
			const int thickness;
			const int lineType;
			const int shift;
		} Draw = {0, 0, 360, cv::Scalar(40, 40, 200), 3, 8, 0};

		void processFrame(cv::Mat& frame, std::string file_name, std::string save_dir, std::string detections_file, bool saveImages);
		std::vector<cv::Rect> detectObjects(cv::Mat& frame, cv::Mat& processedFrame, bool drawDetections);

		inline std::string getFileName(int index);
		inline void saveFrame(cv::Mat& frame, std::string save_dir, std::string file);
		// inline std::string getSaveDirectory();
		inline void displayDetection(cv::Mat& img, cv::Point center, cv::Size size);

		// std::string path;
		CascadeClassifier cascadeClassifier;

	public:

		void readDirectory(const std::string& directory, const std::string& save_dir, const std::string& detections_file, const std::string& classifier_file, bool saveImages);

};

#endif
