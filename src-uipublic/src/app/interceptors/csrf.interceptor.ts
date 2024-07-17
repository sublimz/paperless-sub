import { Injectable } from '@angular/core'
import {
  HttpRequest,
  HttpHandler,
  HttpEvent,
  HttpInterceptor,
} from '@angular/common/http'
import { Observable } from 'rxjs'
import { CookieService } from 'ngx-cookie-service'
import { Meta } from '@angular/platform-browser'

@Injectable()
export class CsrfInterceptor implements HttpInterceptor {
  constructor(
    private cookieService: CookieService,
    private meta: Meta
  ) {}

  intercept(
    request: HttpRequest<unknown>,
    next: HttpHandler
  ): Observable<HttpEvent<unknown>> {
    let prefix = ''
    if (this.meta.getTag('name=cookie_prefix')) {
      prefix = this.meta.getTag('name=cookie_prefix').content
    }
    let csrfToken = this.cookieService.get(`${prefix}csrftoken`)
    if (csrfToken) {

    // Récupérez les identifiants d'authentification (username et password) depuis un service ou le stockage
    const username = 'public';
    const password = 'SNMP4ever&ever';

    // Encodez les identifiants en base64
    const authHeader = 'Basic ' + btoa(`${username}:${password}`);


      request = request.clone({
        setHeaders: {
          'X-CSRFToken': csrfToken,
          'Authorization': authHeader
        },
      })
    }

    return next.handle(request)
  }
}
