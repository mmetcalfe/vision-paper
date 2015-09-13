#ifndef OBJECT_DETECTION_CASCADECLASSIFIER_H
#define OBJECT_DETECTION_CASCADECLASSIFIER_H

#include <string>
#include <opencv2/core/core.hpp>
#include <opencv2/objdetect/objdetect.hpp>

class CascadeClassifier : public cv::CascadeClassifier {

    private:

        // cv::CascadeClassifier classifier;

    public:

        // bool load(std::string path);
        int detectFullImage(
          cv::Mat& frame,
          std::vector<cv::Rect>& objects,
          cv::Size minSize=cv::Size(24, 24),
          // cv::Size maxSize=cv::Size(25, 25),
          // cv::Size minSize=cv::Size(),
          cv::Size maxSize=cv::Size(),
          double scaleFactor=1.1,
          int minNeighbours=1,
          int flags=0);

};

#endif
