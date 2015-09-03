#include "CascadeClassifier.h"

/**
 * Attempts to load a classifier from the specified path.
 *
 * @param path The path to the cascade classifier.
 * @return If the load operation was successful.
 */
bool CascadeClassifier::load(std::string path) {
    return classifier.load(path);
}

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
void CascadeClassifier::detect(cv::Mat& image, std::vector<cv::Rect>& objects, cv::Size minSize, cv::Size maxSize, double scaleFactor, int minNeighbours, int flags) {
    classifier.detectMultiScale(image, objects, scaleFactor, minNeighbours, flags, minSize, maxSize);
}
