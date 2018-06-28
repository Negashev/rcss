### RCSS

Rancher cleanup stacks & services

# install 

you can use health check

```yaml
version: '2'
services:
  rcss:
    image: negash/rcss
    environment:
      CLEANUP_SERVICE_IN_STACKS: Allure,my-app-allure-reports # remove services from stack `Allure` and `my-app-allure-reports` olders $STAY_TIME days (in seconds)
      STAY_TIME: 7 # old days for remove
      CLEANUP_STACKS: my-stack-,test-stack- # remove stack startswith my-stack-* and test-stack-* older $CLEANUP_SERVICE_IN_STACKS days (in seconds)  
      STAY_TIME_STACK: 0.25 # old days for remove
      ENVIRONMENT: 1a5
    labels:
      io.rancher.container.create_agent: 'true' # auto add env for gdapi  
```