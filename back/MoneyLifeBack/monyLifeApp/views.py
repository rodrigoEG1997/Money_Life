from django.shortcuts import render
from django.contrib.auth.models import User, Group
from rest_framework import viewsets
from rest_framework import permissions
from .serializers import *
from .models import *
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from decimal import Decimal
from rest_framework.renderers import JSONRenderer
from django.http import JsonResponse
import json
import re
import random
import math
#Login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login, logout
from monyLifeApp import scripts

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    #authentication_classes = {TokenAuthentication,}
    #permission_classes = {IsAuthenticated,}

    @action(methods=['get', 'post'], detail=False)
    def login(self, request):
        userData = request.data
        user = authenticate(username=userData['username'], password=userData['password'])
        if user == None:
            return JsonResponse({'mensaje': "Usuario o contrasena incorrecta"}, safe = False)
        return JsonResponse({'id': user.id, 'username': user.username}, safe = False)

###################################################################
#LOGICA DE EVENTOS

class EventoViewSet(viewsets.ModelViewSet):
    queryset = Evento.objects.all()
    serializer_class = EventoSerializer

    #Se llama al inicio del turno
    @action(methods=['get', 'post'], detail=False)
    def inicioTurno(self, request):
        jsonUser = request.data
        user = User.objects.filter(id = jsonUser['UserID']).first() 
        turno = Turnos.objects.filter(User=user).first()
        eventos = scripts.seleccionEvento(user)
        output = json.dumps(eventos)
        response = json.loads(output)
        scripts.getAfectaEvento(response)
        scripts.modifyEvento(user, response) #Modifica la frcuencia del evento que se utilizo
        afectaList = scripts.eventoAfecta(user, response) #Crea los afecta del evento que se utilizo
        afectaEventos = Afecta_user.objects.filter(id__in=afectaList)
        scripts.afectaTurnoinstantaneo(afectaEventos, turno)

        return JsonResponse(response, safe = False)

###################################################################

###################################################################
class PreguntaViewSet(viewsets.ModelViewSet):
    queryset = Preguntas.objects.all()
    serializer_class = PreguntasSerializer

    @action(methods=['get', 'post'], detail=False)
    def getPreguntas(self, request):
        jsonUser = request.data
        user = User.objects.filter(id = jsonUser['UserID']).first()

        preguntas = scripts.seleccionPregunta(user)
        output = json.dumps(preguntas)
        response = json.loads(output)
        scripts.getAfectaPregunta(response)
        return JsonResponse(response, safe = False)

    @action(methods=['put'], detail=False)
    def afectaPreguntas(self, request):
        jsonPregunta = request.data
        
        user = User.objects.filter(id = jsonPregunta['UserID']).first()
        turno = Turnos.objects.filter(User=user).first()
        pregunta = Preguntas.objects.filter(id = jsonPregunta['PreguntaID']).first()
        
        if scripts.validarPregunta(user, pregunta):
            scripts.modifyPregunta(user, pregunta) #Modifica la frcuencia de la pregunta que se utilizo
            afectaList = scripts.preguntaAfecta(user, pregunta)
            afectasPregunta = Afecta_user.objects.filter(id__in=afectaList)
            scripts.afectaTurnoinstantaneo(afectasPregunta, turno)
        else:
            return JsonResponse({"mensaje":"No cuentas con los requisitos necesarios para esta acción"}, safe=False)

        if turno.Felicidad >= Decimal(100):
            turno.Felicidad = Decimal(99.9)
        if turno.Felicidad <= Decimal(1):
            turno.Felicidad = Decimal(1)
        sueldoActual = Afecta_user.objects.filter(User=user, Afecta='SueldoReal').first()
        turno.Sueldo = Decimal(sueldoActual.Cantidad)
        turno.save()
        queryset = Turnos.objects.filter(User=user)
        serializer = TurnosSerializer(queryset, many=True)
        return JsonResponse(serializer.data, safe=False)



###################################################################

###################################################################
#LOGICA DE TURNOS

class TurnosViewSet(viewsets.ModelViewSet):
    queryset = Turnos.objects.all()
    serializer_class = TurnosSerializer

    #Este servicio se manda cada que inicie el turno
    @action(methods=['get', 'post'], detail=False)  #se necesita el usuario
    def inicio(self, request):    
        print("INICIASTE TURNOOOOOOOO")    
        jsonTurno = request.data
        user = User.objects.filter(id = jsonTurno["UserID"]).first()
        turno = Turnos.objects.filter(User=user).first()
        prestamos = Prestamo.objects.filter(User=user)
        inversiones = Inversion.objects.filter(User=user)
        inversionesPregunta = InversionPregunta.objects.filter(User = user)

        scripts.afectaTurnos(user, turno) #Llama a todos los afecta que esten relacionados con el usuario y los aplica
        scripts.prestamosTurnos(user, turno, prestamos) #Llama a todos los prestamos relacionados con este usuario para aplicar el gasto
        scripts.inversionesTurnos(user, turno, inversiones) #Llama a todas las inversiones relacionados con este usuario y aplica su flujo
        scripts.inversionesPreguntasTurnos(user, turno, inversionesPregunta)
        scripts.turnoIngresosEgresos(user, turno) #Calcula los ingresos y egresos mensuales de este turno

        sueldoActual = Afecta_user.objects.filter(User=user, Afecta='SueldoReal').first()
        turno.Sueldo = Decimal(sueldoActual.Cantidad)
        turno.NumeroTurnos = turno.NumeroTurnos + 1
        if turno.Felicidad >= Decimal(100):
            turno.Felicidad = Decimal(99.9)
        if turno.Felicidad <= Decimal(1):
            turno.Felicidad = Decimal(1)
        turno.save()

        queryset = Turnos.objects.filter(User=user)
        serializer = TurnosSerializer(queryset, many=True)
        return JsonResponse(serializer.data, safe=False)

    @action(methods=['get', 'post'], detail=False)  #se necesita el usuario
    def intermedio(self, request):
        jsonTurno = request.data
        user = User.objects.filter(id = jsonTurno["UserID"]).first()
        turno = Turnos.objects.filter(User=user).first()

        scripts.turnoIngresosEgresos(user, turno)

        if turno.Felicidad >= Decimal(100):
            turno.Felicidad = Decimal(99.9)
        if turno.Felicidad <= Decimal(1):
            turno.Felicidad = Decimal(1)
        turno.save()

        queryset = Turnos.objects.filter(User=user)
        serializer = TurnosSerializer(queryset, many=True)
        return JsonResponse(serializer.data, safe=False)

    @action(methods=['get', 'post'], detail=False)  #se necesita el usuario
    def felicidad(self, request):
        jsonFelicidad = request.data
        user = User.objects.filter(id = jsonFelicidad["UserID"]).first()

        afecta = Afecta_user.objects.filter(User=user)

        felicidad = []

        for afectaFelicidad in afecta:
            if str(afectaFelicidad.Afecta) == 'Felicidad':
                periodo = Periodo.objects.filter(Turnos=afectaFelicidad.TurnosEsperar).first()
                duracion = str(afectaFelicidad.Duracion)
                if afectaFelicidad.Duracion > 1000:
                    duracion = "infinito"
                felicidad.append({"Decripcion":afectaFelicidad.Descripcion, "Cantidad":afectaFelicidad.Cantidad, "Periodo":periodo.TipoPeriodo, "Duracion":duracion})
  
        return JsonResponse(felicidad, safe=False)


###################################################################

###################################################################

class PrestamoViewSet(viewsets.ModelViewSet):
    queryset = TipoPrestamo.objects.all()
    serializer_class = PrestamosSerializer


    @action(methods=['get', 'post'], detail=False)
    def catalogo(self, request):
        queryset = TipoPrestamo.objects.all()
        serializer = PrestamosSerializer(queryset, many=True)
        return JsonResponse(serializer.data, safe=False)

    @action(methods=['put'], detail=False)
    def Realizar(self, request):
        jsonPrestamo = request.data

        minimoAprobatorio = jsonPrestamo["ValorTotal"] * .10

        if jsonPrestamo["Enganche"] < minimoAprobatorio:
            return JsonResponse({"mensaje": "El enganche no puede ser menor al 10 porciento del valor total"}, safe=False)

        if jsonPrestamo["Enganche"] >= jsonPrestamo["ValorTotal"]:
            return JsonResponse({"mensaje": "El enganche es mayor al préstamo pedido"}, safe=False)

        user = User.objects.filter(id = jsonPrestamo["UserID"]).first()
        turno = Turnos.objects.filter(User=user).first()
        tipoPrestamo = TipoPrestamo.objects.filter(idPrestamo = jsonPrestamo["PrestamoID"]).first()
        cantidadPrestada = jsonPrestamo["ValorTotal"] - jsonPrestamo["Enganche"]

        if Decimal(jsonPrestamo["Enganche"]) >= turno.DineroEfectivo:
            return JsonResponse({"mensaje": "No cuentas con el dinero para realizar esta acción"}, safe=False)

        interes = re.sub('%', '',str(tipoPrestamo.TazaInteres) )
        interes = float(interes)/100
        anos = (tipoPrestamo.Duracion).split(" ")
        anos = int(anos[0])
        pagoMensual = cantidadPrestada/((1 - (pow((1 + (interes/12)), (-(anos*12)))))/(interes/12))
        interesMensual = cantidadPrestada*(interes/12)

        if (turno.Ingresos - turno.Egresos) < pagoMensual:
            return JsonResponse({"mensaje": "No cuentas con los ingresos necesarios para realizar este pedido"}, safe=False)

        prestamoUser = Prestamo(User=user, idPrestamo=tipoPrestamo, ValorTotal=jsonPrestamo["ValorTotal"], CantidadPrestada=cantidadPrestada, Enganche=jsonPrestamo["Enganche"], Frecuencia=3, Amortizacion=0, Interes=interesMensual, Mensualidad=pagoMensual, AbonoCapital=0, SaldoAbsoluto=cantidadPrestada )
        prestamoUser.save()

        turno.DineroEfectivo = turno.DineroEfectivo + Decimal(jsonPrestamo["ValorTotal"])
        turno.DineroEfectivo = turno.DineroEfectivo - Decimal(jsonPrestamo["Enganche"])
        turno.save()
        return JsonResponse({"mensaje":"Se a realizado el prestamo de forma exitosa"}, safe=False)

    @action(methods=['put'], detail=False)
    def Amortizacion(self, request):
        jsonPrestamo = request.data

        user = User.objects.filter(id = jsonPrestamo["UserID"]).first()
        turno = Turnos.objects.filter(User=user).first()
        prestamo = Prestamo.objects.filter(id = jsonPrestamo["PrestamoID"], User = user).first()
        
        if prestamo.SaldoAbsoluto < Decimal(jsonPrestamo["Amortizacion"]):
            return JsonResponse({"mensaje": "El saldo absoluto es menos que la amortización"}, safe=False)
        
        #print("Dinero de turno = ", turno.DineroEfectivo)

        if turno.DineroEfectivo <= Decimal(jsonPrestamo["Amortizacion"]):
            return JsonResponse({"mensaje": "No tienes la cantidad requerida para esta acción"}, safe=False)

        if Decimal(jsonPrestamo["Amortizacion"]) <= 0:
            return JsonResponse({"mensaje": "Cantidad no valida"}, safe=False)

        prestamo.AbonoCapital = Decimal(jsonPrestamo["Amortizacion"]) + prestamo.AbonoCapital

        prestamo.SaldoAbsoluto = prestamo.SaldoAbsoluto - Decimal(jsonPrestamo["Amortizacion"])

        if prestamo.SaldoAbsoluto < prestamo.Mensualidad:
            prestamo.Mensualidad = prestamo.SaldoAbsoluto

        prestamo.save()

        print("Saldo Absoluto = ",prestamo.SaldoAbsoluto)

        if prestamo.SaldoAbsoluto <= 1:
            prestamo.delete()
        
        turno.DineroEfectivo = turno.DineroEfectivo - Decimal(jsonPrestamo["Amortizacion"])
        turno.save()
        return JsonResponse({"mensaje":"Se realizo la amoritizacion de forma correcta"}, safe=False)
    
    @action(methods=['get', 'post'], detail=False)
    def prestamosActuales(self, request):
        jsonInversion = request.data
        user = User.objects.filter(id = jsonInversion['UserID']).first()
        actuales = Prestamo.objects.filter(User=user)
        

        prestamosActuales = []
        
        for prestamo in actuales:
            Preguntas_Requisitos
            ################################################################################
            tipoPrestamo = TipoPrestamo.objects.filter(id = prestamo.idPrestamo.id).first()
            interes = re.sub('%', '',str(tipoPrestamo.TazaInteres) )
            interes = float(interes)/100
            anos = (tipoPrestamo.Duracion).split(" ")
            anos = int(anos[0])
            pagoMensual = float(prestamo.Mensualidad)
            interesMensual = float(prestamo.SaldoAbsoluto)*(interes/12)

            mesesRestantes = 0
            acomulado = 0
            while acomulado + 5 <= float(prestamo.SaldoAbsoluto):
                acomulado = acomulado + (pagoMensual - interesMensual)
                interesMensual = float(float(prestamo.SaldoAbsoluto) - acomulado)*(interes/12)
                mesesRestantes = mesesRestantes + 1
            ################################################################################

            prestamosActuales.append({'PrestamoID':prestamo.id, 'TipoPrestamo':tipoPrestamo.TipoPrestamo, 'Mensualidad':prestamo.Mensualidad, "SaldoAbsoluto":prestamo.SaldoAbsoluto, "MesesRestantes":mesesRestantes})
        
        return JsonResponse(prestamosActuales, safe=False)


###################################################################

###################################################################
class InversionViewSet(viewsets.ModelViewSet):
    queryset = TipoInversiones.objects.all()
    serializer_class = TipoInversionesSerializer

    @action(methods=['get', 'post'], detail=False)
    def catalogoDisponibles(self, request):
        jsonInversion = request.data
        user = User.objects.filter(id = jsonInversion['UserID']).first()
        actuales = Inversion.objects.filter(User=user)
        catalogo = TipoInversiones.objects.all()

        for inversionActual in actuales:
            catalogo = catalogo.exclude(id=inversionActual.TipoInversion.id)

        catalogoActual = []

        for empresa in catalogo:
            riesgo = scripts.riesgoInversion(empresa.RangoRendimiento)
            catalogoActual.append({"id": empresa.id, "Inversion": empresa.Inversion, "TipoInversion": empresa.TipoInversion, "RangoRendimiento": riesgo})

        return JsonResponse(catalogoActual, safe=False)

    @action(methods=['get', 'post'], detail=False)
    def inversionesActuales(self, request):
        jsonInversion = request.data
        user = User.objects.filter(id = jsonInversion['UserID']).first()
        actuales = Inversion.objects.filter(User=user)

        queryset = actuales
        serializer = InversionesSerializer(queryset, many=True)
        return JsonResponse(serializer.data, safe=False)
    
    @action(methods=['get', 'post'], detail=False)
    def inversionesPersonalesActuales(self, request):
        jsonInversion = request.data
        user = User.objects.filter(id = jsonInversion['UserID']).first()

        #inversionesAfecta = Afecta_user.objects.filter(Afecta__startswith = 'Inversion', User = user.id)
        inversionPregunta = InversionPregunta.objects.filter(User = user.id)

        inversiones = []

        """
        for afecta in inversionesAfecta:
            periodo = Periodo.objects.filter(Turnos=afecta.TurnosEsperar).first()
            inversiones.append({'id':afecta.id, 'TipoInversion': 'FlujoEfectivo', 'Descripcion':afecta.Descripcion, 'Cantidad':afecta.Cantidad, 'Periodo': periodo.TipoPeriodo})
        """
        for inverPregunta in inversionPregunta:
            inversiones.append({'id':inverPregunta.id, 'TipoInversion':'GananciaCapital', 'Descripcion':inverPregunta.Descripcion, 'Inicio':inverPregunta.SaldoInicial, 'Actual':inverPregunta.SaldoActual})

        return JsonResponse(inversiones, safe=False)
    
    @action(methods=['post'], detail=False)
    def nueva(self, request):
        jsonInversion = request.data
        user = User.objects.filter(id = jsonInversion['UserID']).first()
        turno = Turnos.objects.filter(User=user).first()
        compania = TipoInversiones.objects.filter(id=jsonInversion["InversionID"]).first()

        if turno.DineroEfectivo < Decimal(jsonInversion['Cantidad']):
            return JsonResponse({"mensaje": "No cuentas con el dinero para realizar esta acción"}, safe=False)
        
        if Decimal(jsonInversion['Cantidad']) < 100:
            return JsonResponse({"mensaje": "Valor no válido para realizar esta acción"}, safe=False)

        rangoRendimiento = (compania.RangoRendimiento).split(" ")
        limite_inferior = float(rangoRendimiento[0])
        limite_superior = float(rangoRendimiento[2])
        tasaRendimiento = random.uniform(limite_inferior,limite_superior)
        nuvaInversion = Inversion(User=user,TipoInversion=compania,NombreInversion=compania.Inversion,TipoEmpresa=compania.TipoInversion,SaldoInicial=jsonInversion['Cantidad'],SaldoAportacion=jsonInversion['Cantidad'],EventoExterno=0,TasaRendimiento=tasaRendimiento,Aportacion=0,SaldoActual=jsonInversion['Cantidad'])
        nuvaInversion.save()

        turno.DineroEfectivo = turno.DineroEfectivo - Decimal(jsonInversion['Cantidad'])
        turno.save()

        return JsonResponse({"mensaje":"Se realizo la nueva inversion de forma exitosa"}, safe=False)

    @action(methods=['put'], detail=False)
    def agregarDinero(self, request):
        jsonInversion = request.data
        user = User.objects.filter(id = jsonInversion['UserID']).first()
        turno = Turnos.objects.filter(User=user).first()

        inversion = Inversion.objects.filter(id=jsonInversion["InversionID"]).first()
        
        if jsonInversion["Cantidad"] > turno.DineroEfectivo:
            return JsonResponse({"mensaje":"No cuentas con la cantidad de dinero para realizar esta acción"}, safe=False)

        if jsonInversion["Cantidad"] <= 0:
            return JsonResponse({"mensaje":"Cantidad no valida"}, safe=False)

        inversion.SaldoAportacion = inversion.SaldoAportacion + jsonInversion["Cantidad"]
        inversion.SaldoActual = inversion.SaldoActual + jsonInversion["Cantidad"]
        inversion.save()

        turno.DineroEfectivo = turno.DineroEfectivo - Decimal(jsonInversion["Cantidad"])
        turno.save()
        
        return JsonResponse({"mensaje": "Se realizo la transacción de forma correcta"}, safe=False)

    @action(methods=['put'], detail=False)
    def retirarDinero(self, request):
        jsonInversion = request.data
        user = User.objects.filter(id = jsonInversion['UserID']).first()
        turno = Turnos.objects.filter(User=user).first()
        inversion = Inversion.objects.filter(id=jsonInversion["InversionID"]).first()

        if jsonInversion["Cantidad"] >= inversion.SaldoActual:
            return JsonResponse({"mensaje":"No cuentas con suficiente dinero para retirar esta cantidad"}, safe=False)

        if jsonInversion["Cantidad"] <= 0:
            return JsonResponse({"mensaje":"Cantidad no valida"}, safe=False)

        inversion.Aportacion = inversion.Aportacion + jsonInversion["Cantidad"]
        inversion.SaldoActual = inversion.SaldoActual - Decimal(jsonInversion["Cantidad"])
        inversion.save()

        turno.DineroEfectivo = turno.DineroEfectivo + Decimal(jsonInversion["Cantidad"])
        turno.save()
        
        return JsonResponse({"mensaje": "La transacción se realizo de forma correcta"}, safe=False)

    @action(methods=['put'], detail=False)
    def retirarAccion(self, request):
        jsonInversion = request.data
        user = User.objects.filter(id = jsonInversion['UserID']).first()
        turno = Turnos.objects.filter(User=user).first()
        inversion = Inversion.objects.filter(id=jsonInversion["InversionID"]).first()

        turno.DineroEfectivo = turno.DineroEfectivo + inversion.SaldoActual
        inversion.delete()
        turno.save()
        
        return JsonResponse({"mensaje": "Se retiro la acción de forma correcta"}, safe=False)

    @action(methods=['put'], detail=False)
    def retirarInversionPersonal(self, request):
        jsonInversion = request.data
        user = User.objects.filter(id = jsonInversion['UserID']).first()
        turno = Turnos.objects.filter(User=user).first()
        inversion = InversionPregunta.objects.filter(id=jsonInversion["InversionID"]).first()

        turno.DineroEfectivo = turno.DineroEfectivo + inversion.SaldoActual
        inversion.delete()
        turno.save()
        
        return JsonResponse({"mensaje": "Se retiro la acción de forma correcta"}, safe=False)

###################################################################

###################################################################
class PortafolioViewSet(viewsets.ModelViewSet):

    @action(methods=['get', 'post'], detail=False)
    def financiero(self, request):
        jsonPortafolio = request.data
        user = User.objects.filter(id = jsonPortafolio['UserID']).first()
        turno = Turnos.objects.filter(User=user).first()
        prestamos = Prestamo.objects.filter(User = user.id)
        inversiones = Inversion.objects.filter(User = user.id)
        ingresos = Afecta_user.objects.filter(Afecta = 'Ingresos', User = user.id)
        egresos = Afecta_user.objects.filter(Afecta = 'Egresos', User = user.id)
        inversionesAfecta = Afecta_user.objects.filter(Afecta__startswith = 'Inversion', User = user.id)
        inversionPregunta = InversionPregunta.objects.filter(User = user.id)

        portafolio = {'Egresos':[], 'Ingresos':[]}

        portafolio['Ingresos'].append({"Tipo":"Ingreso", "Nombre":"Sueldo","Cantidad":turno.Sueldo, "Periodo":"Mensual"})
        portafolio['Egresos'].append({"Tipo":"Egreso", "Nombre":"Gastos Personales", "Cantidad":8000, "Periodo":"Mensual"})

        for prestamo in prestamos:
            nombrePrestamo = TipoPrestamo.objects.filter(idPrestamo = prestamo.idPrestamo.id).first()
            nombre = "Préstamo " + str(nombrePrestamo.TipoPrestamo)
            portafolio['Egresos'].append({"Tipo":"Egreso", "Nombre":nombre, "Cantidad":prestamo.Mensualidad, "Periodo":"Mensual"})
        """
        for inversion in inversiones:
            compania = TipoInversiones.objects.filter(id=inversion.TipoInversion.id).first()
            portafolio['Ingresos'].append({"Tipo":"Ingreso", "Nombre":compania.Inversion, "Cantidad":inversion.SaldoActual, "Periodo":"Activo"})
        """
        for ingreso in ingresos:
            periodo = Periodo.objects.filter(Turnos=ingreso.TurnosEsperar).first()
            portafolio['Ingresos'].append({"Tipo":"Ingreso", "Nombre":ingreso.Descripcion, "Cantidad":ingreso.Cantidad, "Periodo":periodo.TipoPeriodo})

        for egreso in egresos:
            periodo = Periodo.objects.filter(Turnos=egreso.TurnosEsperar).first()
            portafolio['Egresos'].append({"Tipo":"Egreso", "Nombre":egreso.Descripcion, "Cantidad":egreso.Cantidad, "Periodo":periodo.TipoPeriodo})

        
        for invercionAfe in inversionesAfecta:
            periodo = Periodo.objects.filter(Turnos=invercionAfe.TurnosEsperar).first()
            portafolio['Ingresos'].append({"Tipo":"Ingreso", "Nombre":invercionAfe.Descripcion, "Cantidad":invercionAfe.Cantidad, "Periodo":periodo.TipoPeriodo})
        """
        for inversionPreg in inversionPregunta:
            tipoInversion = TipoPregunta.objects.filter(id=inversionPreg.TipoInversion.id).first()
            portafolio['Ingresos'].append({"Tipo":"Ingreso", "Nombre":tipoInversion.TipoPregunta, "Cantidad":inversionPreg.SaldoActual, "Periodo":"Activo"})
        """
        return JsonResponse(portafolio, safe=False)

    
###################################################################

###################################################################
class FinJuegoViewSet(viewsets.ModelViewSet):

    @action(methods=['put'], detail=False)
    def juego(self, request):
        print("ESTAN LLAMANDO A FIN DEL JUEGO")
        jsonUser = request.data
        user = User.objects.filter(id = jsonUser['UserID']).first()

        scripts.borrarInfoUser(user)
        scripts.reiniciarUser(user)

        return JsonResponse({"mensaje":"Fin del juego"}, safe=False)



###################################################################

###################################################################

class PruebaViewSet(viewsets.ViewSet):

    @action(methods=['get'], detail=False)
    def prueba2(self, request):
        print("ENTRO A PRUEBA 2")
        pru = Prueba(EventoID=1, Descripcion="Prueba1", Periodo="Semana", Duracion=10)
        print(pru)
        serializer = PruebaSerializer(pru)
        return JsonResponse(serializer.data, safe=False)
    
