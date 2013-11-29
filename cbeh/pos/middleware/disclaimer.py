from django.http import HttpResponseRedirect

class DisclaimerMiddleware(object):
    
    def process_request(self, request):
        # Check if the user has already agreed to the site disclaimer
        # If not, redirect to the home/disclaimer page
        
        requestPath = request.path # Get the URL path

        if requestPath == '/cbeh/pos/home/': # Continue to the Home page
            return None
        # Check if a disclaimer cookie exists, and if so has the user already agreed
        elif request.COOKIES.has_key('pos_disclaimer_cookie') and requestPath != '/cbeh/pos/home/':
            value = request.COOKIES['pos_disclaimer_cookie']
            if value != 'has_agreed':
                return HttpResponseRedirect('/cbeh/pos/home')
            else:
                return None # Continue to the user's page of choice
        else:
        # Set the redirect to the home page as there is no disclaimer cookie yet (i.e. new session)
            response = HttpResponseRedirect('/cbeh/pos/home')
            response.set_cookie('pos_disclaimer_cookie', 'has_not_agreed') # Overwrites any existing cookie with the same name
            response.set_cookie('after_disclaimer_redirect_path', requestPath) # Store the path the user entered, to redirect to after they have agreed
            return response