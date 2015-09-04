#include "opencv2/highgui/highgui.hpp"
#include "opencv2/imgproc/imgproc.hpp"
#include <iostream>
#include <stdio.h>

using namespace cv;

/** @function main */
int main(int argc, char** argv)
{
  Mat src, src_gray;

  std::cout << "/// Read the image" << std::endl;
  src = imread( argv[1], 1 );

  if( !src.data )
    { return -1; }



  std::cout << "/// Convert it to gray" << std::endl;
  cvtColor( src, src_gray, CV_BGR2GRAY );

  std::cout << "/// Reduce the noise so we avoid false circle detection" << std::endl;
  int blurAmount = src_gray.rows * 0.002;
  blurAmount += (blurAmount % 2) + 1;
  GaussianBlur( src_gray, src_gray, Size(blurAmount, blurAmount), 2, 2 );

  vector<Vec3f> circles;

  std::cout << "/// Apply the Hough Transform to find the circles" << std::endl;
  int minDist = src_gray.rows * 0.05;
  int upperCannyThreshold = 150; // 200
  int centerDetectThreshold = 90; // 100
  int min_radius = src_gray.rows * 0.05;
  int max_radius = 0;
  std::cout << "src_gray.rows: " << src_gray.rows << std::endl;
  std::cout << "minDist: " << minDist << std::endl;
  std::cout << "upperCannyThreshold: " << upperCannyThreshold << std::endl;
  std::cout << "centerDetectThreshold: " << centerDetectThreshold << std::endl;
  std::cout << "min_radius: " << min_radius << std::endl;
  std::cout << "max_radius: " << max_radius << std::endl;
  HoughCircles( src_gray, circles, CV_HOUGH_GRADIENT, 1, minDist, upperCannyThreshold, centerDetectThreshold, min_radius, max_radius);

  std::cout << "/// Draw the circles detected" << std::endl;
  for( size_t i = 0; i < circles.size(); i++ )
  {
      Point center(cvRound(circles[i][0]), cvRound(circles[i][1]));
      int radius = cvRound(circles[i][2]);
      // circle center
      circle( src_gray, center, 3, Scalar(0,255,0), -1, 8, 0 );
      // circle outline
      circle( src_gray, center, radius, Scalar(0,0,255), 3, 8, 0 );
   }

  std::cout << "/// Show your results" << std::endl;
  namedWindow( "Hough Circle Transform Demo", CV_WINDOW_AUTOSIZE );
  imshow( "Hough Circle Transform Demo", src_gray );

  waitKey(0);
  return 0;
}
