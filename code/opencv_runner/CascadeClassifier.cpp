#include "CascadeClassifier.h"
#include <opencv2/imgproc/imgproc.hpp>

// /**
//  * Attempts to load a classifier from the specified path.
//  *
//  * @param path The path to the cascade classifier.
//  * @return If the load operation was successful.
//  */
// bool CascadeClassifier::load(std::string path) {
//     return classifier.load(path);
// }

/**
 * Detects objects of different sizes in the input image.
 *
 * @param image The image where objects are being detected.
 * @param objects Vector of rectangles where each rectangle contains the detected object.
 * @param minSize Minimum possible object size. Objects smaller than that are ignored.
 * @param maxSize Maximum possible object size. Objects larger than that are ignored.
 * @param scaleFactor Specifies how much the image size is reduced at each image scale.
 * @param minNeighbors Specifies how many neighbors each candidate rectangle should have to retain it.
 * @param flags Parameter with the same meaning for an old cascade as in the function cvHaarDetectObjects. It is not used for a new cascade.
 */
int CascadeClassifier::detect(cv::Mat& image, std::vector<cv::Rect>& objects, cv::Size minSize, cv::Size maxSize, double scaleFactor, int minNeighbours, int flags) {
    // classifier.detectMultiScale(image, objects, scaleFactor, minNeighbours, flags, minSize, maxSize);

    cv::Mat& scaledImage = image;

    // cv::Mat scaledImage;
    // cv::Size classifierSize = data.origWinSize;
    // cv::resize(image, scaledImage, classifierSize, 0, 0, cv::INTER_LINEAR);

    cv::Size size(scaledImage.cols, scaledImage.rows);

    // Need to set image first, see:
    // http://docs.opencv.org/modules/objdetect/doc/cascade_classification.html#featureevaluator-setimage
    bool success = featureEvaluator->setImage(scaledImage, size);

    if (!success) {
        CV_Assert(false);
        return 0;
    }

    // Once once over the whole image
    double gypWeight;
    int result = runAt(this->featureEvaluator, cv::Point(0, 0), gypWeight);

    if (result == 1) {
        cv::Rect rect = {0, 0, 24, 24}; // {x, y, w, h}
        objects.push_back(rect);
    }

    return result;
}
