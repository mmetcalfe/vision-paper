data <- read.delim("WaEx7.9.txt")

# summary(bincloglog <- glm(cbind(NumKilled,NumBeetles-NumKilled)~LogDose, data=data, family=binomial(link="cloglog")))
# summary(binprobit <- glm(cbind(NumKilled,NumBeetles-NumKilled)~LogDose, data=data, family=binomial(link="probit")))
# summary(binlogit <- glm(cbind(NumKilled,NumBeetles-NumKilled)~LogDose, data=data, family=binomial(link="logit")))
#
# par(mfrow=c(1,1))
# plot(data$LogDose,data$NumKilled/data$NumBeetles,cex=sqrt(data$NumBeetles)/4)
# mk.pred <- function(fit){
#   function(x) predict(fit, newdata=data.frame(LogDose=x), type="response")
# }
# curve(mk.pred(bincloglog)(x), add=TRUE, col=4)
# curve(mk.pred(binprobit)(x), add=TRUE,col=3)
# curve(mk.pred(binlogit)(x), add=TRUE, col=2)
#
#
# par(mfrow=c(2,2))
# plot(bincloglog)
# plot(binprobit)
# plot(binlogit)
